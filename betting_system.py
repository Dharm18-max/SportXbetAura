"""
Betting System Core Module (Same as original)
"""

import heapq
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict


class BettingEvent:
    """Represents a sports betting event."""
    
    def __init__(self, event_id: str, sport: str, teams: Tuple[str, str], 
                 odds: Tuple[float, float], date: str):
        self.event_id = event_id
        self.sport = sport
        self.teams = teams
        self.odds = odds
        self.date = date
        self.status = "OPEN"
        self.bets_count = 0
        self.total_wagered = 0.0


class Bet:
    """Represents a single bet placed by user."""
    
    def __init__(self, bet_id: str, event_id: str, amount: float, 
                 odds: float, team_choice: str):
        self.bet_id = bet_id
        self.event_id = event_id
        self.amount = amount
        self.odds = odds
        self.team_choice = team_choice
        self.timestamp = datetime.now()
        self.status = "PENDING"
        self.potential_winnings = amount * odds


class BettingSystem:
    """Sports betting system."""
    
    def __init__(self):
        self.events: Dict[str, BettingEvent] = {}
        self.bets: Dict[str, Bet] = {}
        self.user_balance = 1000.0
        self.betting_history = []
        self.bet_counter = 0
        self.odds_cache = {}
    
    def add_event(self, event_id: str, sport: str, teams: Tuple[str, str],
                  odds: Tuple[float, float], date: str) -> bool:
        if event_id not in self.events:
            self.events[event_id] = BettingEvent(event_id, sport, teams, odds, date)
            return True
        return False
    
    def place_bet(self, event_id: str, amount: float, team_idx: int) -> bool:
        if event_id not in self.events:
            return False
        
        if amount > self.user_balance:
            return False
        
        event = self.events[event_id]
        odds = event.odds[team_idx]
        team = event.teams[team_idx]
        
        self.bet_counter += 1
        bet_id = f"BET_{self.bet_counter:04d}"
        bet = Bet(bet_id, event_id, amount, odds, team)
        
        self.bets[bet_id] = bet
        self.betting_history.append(bet)
        self.user_balance -= amount
        
        event.bets_count += 1
        event.total_wagered += amount
        
        return True
    
    def undo_last_bet(self) -> bool:
        if not self.betting_history:
            return False
        
        bet = self.betting_history.pop()
        self.user_balance += bet.amount
        
        if bet.event_id in self.events:
            event = self.events[bet.event_id]
            event.bets_count -= 1
            event.total_wagered -= bet.amount
        
        del self.bets[bet.bet_id]
        return True
    
    def calculate_parlay(self, parlay_bets: List[Tuple[float, float]]) -> dict:
        if not parlay_bets or len(parlay_bets) < 2:
            return {}
        
        dp_odds = [0.0] * len(parlay_bets)
        dp_odds[0] = parlay_bets[0][1]
        
        for i in range(1, len(parlay_bets)):
            dp_odds[i] = dp_odds[i-1] * parlay_bets[i][1]
        
        total_investment = sum(amount for amount, _ in parlay_bets)
        final_odds = dp_odds[-1]
        total_winnings = total_investment * final_odds
        profit = total_winnings - total_investment
        roi = (profit / total_investment) * 100 if total_investment > 0 else 0
        
        return {
            'total_investment': total_investment,
            'total_odds': final_odds,
            'total_winnings': total_winnings,
            'profit': profit,
            'roi': roi,
            'num_bets': len(parlay_bets)
        }
