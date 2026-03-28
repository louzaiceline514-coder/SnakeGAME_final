#!/usr/bin/env python3

"""Lancement des benchmarks pour tester le système."""

import requests
import json
import time

def run_benchmark():
    base_url = "http://127.0.0.1:8000"
    
    print(" Lancement des benchmarks...")
    
    # Benchmark A*
    print("\n Benchmark A* (50 parties)...")
    start_time = time.time()
    
    try:
        payload = {"episodes": 50, "agent_type": "astar"}
        response = requests.post(f"{base_url}/api/training/start", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            duration = time.time() - start_time
            scores = result.get('scores', [])
            
            print(f" A* terminé en {duration:.2f}s")
            print(f"   Episodes: {result.get('episodes')}")
            print(f"   Scores: {scores[:10]}{'...' if len(scores) > 10 else ''}")
            print(f"   Score moyen: {sum(scores)/len(scores):.2f}")
            print(f"   Meilleur score: {max(scores)}")
        else:
            print(f" Erreur A*: {response.status_code}")
            
    except Exception as e:
        print(f" Erreur A*: {e}")
    
    # Benchmark RL
    print("\n Benchmark RL (50 parties)...")
    start_time = time.time()
    
    try:
        payload = {"episodes": 50, "agent_type": "rl"}
        response = requests.post(f"{base_url}/api/training/start", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            duration = time.time() - start_time
            scores = result.get('scores', [])
            
            print(f" RL terminé en {duration:.2f}s")
            print(f"   Episodes: {result.get('episodes')}")
            print(f"   Scores: {scores[:10]}{'...' if len(scores) > 10 else ''}")
            print(f"   Score moyen: {sum(scores)/len(scores):.2f}")
            print(f"   Meilleur score: {max(scores)}")
        else:
            print(f" Erreur RL: {response.status_code}")
            
    except Exception as e:
        print(f" Erreur RL: {e}")
    
    # Vérification des stats finales
    print("\n Vérification des stats finales...")
    try:
        response = requests.get(f"{base_url}/api/stats/comparison")
        stats = response.json()
        
        print("A* Stats:")
        print(f"   Parties jouées: {stats['astar']['games_played']}")
        print(f"   Score moyen: {stats['astar']['avg_score']:.2f}")
        print(f"   Meilleur score: {stats['astar']['best_score']}")
        print(f"   Taux de survie: {stats['astar']['win_rate']*100:.1f}%")
        
        print("RL Stats:")
        print(f"   Parties jouées: {stats['rl']['games_played']}")
        print(f"   Score moyen: {stats['rl']['avg_score']:.2f}")
        print(f"   Meilleur score: {stats['rl']['best_score']}")
        print(f"   Taux de survie: {stats['rl']['win_rate']*100:.1f}%")
        
    except Exception as e:
        print(f" Erreur stats: {e}")

if __name__ == "__main__":
    run_benchmark()


# ajout lydia
