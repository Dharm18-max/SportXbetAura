"""
SportXBetAura - Flask Backend
=============================
Premium Sports Betting Platform with Advanced DSA
"""

from flask import Flask, render_template, request, jsonify, session
from betting_system import BettingSystem
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sports_betting_secret_key_2026'

# Global betting system
betting_system = BettingSystem()


def init_sample_data():
    """Initialize sample sports events."""
    events_data = [
        ('E001', 'Basketball', ('Lakers', 'Celtics'), (1.85, 2.10), '2026-04-16'),
        ('E002', 'Football', ('Arsenal', 'Liverpool'), (2.80, 1.45), '2026-04-16'),
        ('E003', 'Tennis', ('Federer', 'Nadal'), (1.95, 1.92), '2026-04-17'),
        ('E004', 'Cricket', ('India', 'Australia'), (1.70, 2.30), '2026-04-17'),
        ('E005', 'Baseball', ('Yankees', 'RedSox'), (2.05, 1.80), '2026-04-18'),
        ('E006', 'Hockey', ('Maple Leafs', 'Avalanche'), (1.75, 2.20), '2026-04-18'),
    ]
    
    for event_data in events_data:
        betting_system.add_event(*event_data)


# Initialize sample data
init_sample_data()


@app.route('/')
def home():
    """Home page."""
    return render_template('home.html')


@app.route('/events')
def events():
    """Events page."""
    return render_template('events.html')


@app.route('/api/events', methods=['GET'])
def get_events_api():
    """Get all events as JSON."""
    events_list = []
    for event_id, event in betting_system.events.items():
        events_list.append({
            'id': event.event_id,
            'sport': event.sport,
            'team1': event.teams[0],
            'team2': event.teams[1],
            'odds1': event.odds[0],
            'odds2': event.odds[1],
            'date': event.date,
            'status': event.status,
            'bets': event.bets_count,
            'wagered': round(event.total_wagered, 2)
        })
    
    return jsonify(events_list)


@app.route('/api/place-bet', methods=['POST'])
def place_bet_api():
    """Place a bet via API."""
    data = request.json
    event_id = data.get('event_id')
    amount = float(data.get('amount', 0))
    team_idx = int(data.get('team_idx', 0))
    
    if event_id not in betting_system.events:
        return jsonify({'success': False, 'message': 'Event not found'}), 400
    
    if amount > betting_system.user_balance:
        return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
    
    if betting_system.place_bet(event_id, amount, team_idx):
        event = betting_system.events[event_id]
        team = event.teams[team_idx]
        odds = event.odds[team_idx]
        
        return jsonify({
            'success': True,
            'message': f'Bet placed on {team}',
            'balance': round(betting_system.user_balance, 2),
            'potential_win': round(amount * odds, 2)
        })
    
    return jsonify({'success': False, 'message': 'Failed to place bet'}), 400


@app.route('/api/best-odds', methods=['GET'])
def best_odds_api():
    """Get best odds events."""
    odds_list = []
    
    for event_id, event in betting_system.events.items():
        min_odds = min(event.odds)
        odds_list.append({
            'id': event.event_id,
            'sport': event.sport,
            'team1': event.teams[0],
            'team2': event.teams[1],
            'best_odds': min_odds,
            'date': event.date
        })
    
    # Sort by best odds
    odds_list.sort(key=lambda x: x['best_odds'])
    
    return jsonify(odds_list[:10])


@app.route('/api/history', methods=['GET'])
def history_api():
    """Get betting history."""
    history_list = []
    
    for bet in reversed(betting_system.betting_history):
        history_list.append({
            'id': bet.bet_id,
            'event_id': bet.event_id,
            'amount': round(bet.amount, 2),
            'odds': bet.odds,
            'team': bet.team_choice,
            'potential_win': round(bet.potential_winnings, 2),
            'timestamp': bet.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': bet.status
        })
    
    return jsonify(history_list)


@app.route('/api/undo-bet', methods=['POST'])
def undo_bet_api():
    """Undo the last bet."""
    if betting_system.undo_last_bet():
        return jsonify({
            'success': True,
            'message': 'Last bet undone',
            'balance': round(betting_system.user_balance, 2)
        })
    
    return jsonify({'success': False, 'message': 'No bets to undo'}), 400


@app.route('/api/parlay', methods=['POST'])
def calculate_parlay_api():
    """Calculate parlay."""
    data = request.json
    parlay_bets = data.get('bets', [])
    
    if len(parlay_bets) < 2:
        return jsonify({'success': False, 'message': 'Need at least 2 bets'}), 400
    
    bets_list = [(float(b['amount']), float(b['odds'])) for b in parlay_bets]
    result = betting_system.calculate_parlay(bets_list)
    
    if result:
        return jsonify({
            'success': True,
            'investment': round(result['total_investment'], 2),
            'odds': round(result['total_odds'], 2),
            'potential_winnings': round(result['total_winnings'], 2),
            'profit': round(result['profit'], 2),
            'roi': round(result['roi'], 2)
        })
    
    return jsonify({'success': False, 'message': 'Error calculating parlay'}), 400


@app.route('/api/statistics', methods=['GET'])
def statistics_api():
    """Get user statistics."""
    stats = {
        'balance': round(betting_system.user_balance, 2),
        'total_bets': len(betting_system.bets),
        'total_wagered': round(sum(b.amount for b in betting_system.bets.values()), 2),
        'total_potential': round(sum(b.potential_winnings for b in betting_system.bets.values()), 2),
        'avg_odds': round(sum(b.odds for b in betting_system.bets.values()) / len(betting_system.bets) if betting_system.bets else 0, 2)
    }
    
    return jsonify(stats)


@app.route('/api/compare-odds/<event_id>', methods=['GET'])
def compare_odds_api(event_id):
    """Compare odds for an event."""
    if event_id not in betting_system.events:
        return jsonify({'success': False, 'message': 'Event not found'}), 400
    
    event = betting_system.events[event_id]
    odds1, odds2 = event.odds
    
    # Calculate implied probabilities
    prob1 = (1 / odds1) * 100
    prob2 = (1 / odds2) * 100
    
    return jsonify({
        'success': True,
        'team1': {
            'name': event.teams[0],
            'odds': odds1,
            'probability': round(prob1, 2)
        },
        'team2': {
            'name': event.teams[1],
            'odds': odds2,
            'probability': round(prob2, 2)
        },
        'spread': round(abs(odds1 - odds2), 2),
        'better_team': event.teams[0] if odds1 > odds2 else event.teams[1]
    })


@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    return render_template('dashboard.html')


@app.route('/betting')
def betting():
    """Betting page."""
    return render_template('betting.html')


@app.route('/history')
def history():
    """History page."""
    return render_template('history.html')


@app.route('/parlay')
def parlay():
    """Parlay calculator page."""
    return render_template('parlay.html')


@app.route('/odds-analysis')
def odds_analysis():
    """Odds analysis page."""
    return render_template('odds_analysis.html')


if __name__ == '__main__':
    app.run(debug=False)
