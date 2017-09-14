#!/bin/env python3
import twitter
import networkx as nx
import pickle
import itertools
import numpy as np
import scipy
import plotly.offline as py
import plotly.graph_objs as go



DATA_FILE = 'data/store.pickle'
try:
    store = pickle.load(open(DATA_FILE, 'rb'))
except IOError:
    store = {}


CORNELL_ID = 17369110


api = twitter.Api(consumer_key='redacted',
                  consumer_secret='redacted',
                  access_token_key='redacted',
                  access_token_secret='redacted',
                  sleep_on_rate_limit=False)

# users = api.GetFriends(user_id=CORNELL_ID)
# print([u.screen_name for u in users])

class Main:
    def getUser(self, id):
        if ('user' not in store.setdefault(id, {})):
            print('Calling getUser {}'.format(id))
            user = api.GetUser(user_id=id)
            store[id]['user'] = {'name': user.name, 'screen_name': user.screen_name}
        return store[id]['user']

    def getUserTimeline(self, id):
        user = self.getUser(id)
        if 'timeline' not in store[id]:
            print('Calling timeline for user {}'.format(user['name']))
            store[id]['timeline'] = api.GetUserTimeline(user_id=id, count=200)
        return store[id]['timeline']

    def formatUser(self, id):
        return self.getUser(id)['name']

    def getMentions(self, id):
        # print('Getting mentions for {}'.format(self.formatUser(id)))
        mentions = list(itertools.chain(*[t.user_mentions for t in self.getUserTimeline(id)]))

        for m in mentions:
            if ('user' not in store.setdefault(m.id, {})):
                store[m.id]['user'] = {'name': m.name, 'screen_name': m.screen_name}
            self.nodes.add(self.formatUser(m.id))
            self.edges.add((self.formatUser(id), self.formatUser(m.id)))

        return mentions

    def main(self):
        self.nodes = set()
        self.edges = set()

        for m in self.getMentions(CORNELL_ID):
            self.getMentions(m.id)
        
        # with open('data/edges.csv', 'w') as ft:
        #     ft.write('Source,Target\n')
        #     for edge in edges:
        #         ft.write('"{}","{}"\n'.format(edge[0],edge[1]))

        self.g = nx.Graph()
        self.g.add_nodes_from(self.nodes)
        self.g.add_edges_from(self.edges)


    def add_sink(self):
        self.g.add_node('sink')
        for n in self.g.nodes():
            if n not in [self.formatUser(x.id) for x in self.getMentions(CORNELL_ID)]:
                self.g.add_edge(n, 'sink')


    def calculate_escape(self):
        a = nx.to_numpy_matrix(self.g)
        num_nodes = a.shape[0]
        b = np.array([0] * num_nodes)
        for i,name in enumerate(self.g.nodes()):
            if name == 'sink':
                sink = i
                for j in range(num_nodes):
                    a[i,j] = 0
                a[i,i] = 1
                continue
            if name in ['Cornell University', 'CornellArts&Sciences', 'Cornell Engineering', 'Cornell HumanEcology']:
                cornell = i
                for j in range(num_nodes):
                    a[i,j] = 0
                a[i,i] = 1
                b[i] = 1
                continue
            s = np.count_nonzero(a[i,:])
            a[i,i] = (-s)

        x = np.linalg.solve(a, b)
        return x

    def make_histogram(self, x, name):
        data = [go.Histogram(x=x)]
        # py.plot(go.Figure(data=data,
        #                   layout=go.Layout(xaxis={'type':'log', 'autorange':True})),
        py.plot(data, filename=name)

    def get_results(self, escapes):
        return sorted(zip(self.g.nodes(), escapes), key=lambda x: x[1])

    def make_table(self, vals):
        print('Return Probability | Name')
        print('-'*100)
        for name, prob in vals:
            print('{: <10} | {}'.format(prob,name))

try:
    m = Main()
    m.main()
    m.add_sink()
    x = m.calculate_escape()
    m.make_histogram(x, 'data/histogram2.html')
    # m.make_table(m.get_results(x))
    
finally:
    pickle.dump(store, open(DATA_FILE, 'wb'))


