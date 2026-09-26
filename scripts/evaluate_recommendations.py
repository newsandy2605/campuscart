"""Offline baseline evaluation over exported interaction events. No metrics are reported unless real data is supplied."""
from __future__ import annotations
import argparse, json, math
from collections import defaultdict

POSITIVE={'view','favorite','offer','purchase','message'}

def ndcg(recs, relevant, k):
    dcg=sum((1/math.log2(i+2)) for i,item in enumerate(recs[:k]) if item in relevant)
    ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
    return dcg/ideal if ideal else 0.0

def main():
    p=argparse.ArgumentParser(); p.add_argument('events', nargs='?'); p.add_argument('--input', dest='input_path'); p.add_argument('--k',type=int,default=10); args=p.parse_args(); events=args.input_path or args.events
    if not events: p.error('provide an events JSONL path or --input <path>')
    history=defaultdict(set); targets=defaultdict(set)
    with open(events,encoding='utf-8') as f:
      for line in f:
        e=json.loads(line); uid=e.get('user_id'); lid=e.get('listing_id')
        if uid is None or lid is None: continue
        if e.get('event_type') in POSITIVE: targets[uid].add(lid); history[uid].add(lid)
    if not targets:
      print({'users':0,'ndcg_at_k':None,'note':'No real interaction data found. Export interaction_events first.'}); return
    # This script evaluates a simple popularity baseline from the supplied event data.
    popularity=defaultdict(int)
    for user_items in targets.values():
      for lid in user_items: popularity[lid]+=1
    ranking=[x for x,_ in sorted(popularity.items(), key=lambda kv:(-kv[1],kv[0]))]
    scores=[ndcg(ranking,items,args.k) for items in targets.values()]
    print({'users':len(scores),'ndcg_at_k':sum(scores)/len(scores),'k':args.k,'baseline':'campus-wide interaction popularity'})

if __name__=='__main__': main()
