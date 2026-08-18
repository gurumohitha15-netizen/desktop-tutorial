import sys
import os
import json

# Add current workspace to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_service import DbService
from services.behavior_analyzer import BehaviorAnalyzer
from services.hype_detector import HypeDetector
from services.ai_service import AiService
from services.recommendation_engine import RecommendationEngine

def run_tests():
    print("Initializing test database...")
    db = DbService()
    db.init_db()  # Seed standard dataset
    
    # 1. Test user creation & verification
    user_email = "test_student@college.edu"
    existing = db.get_user_by_email(user_email)
    if existing:
        user_id = existing['id']
    else:
        user_id = db.create_user("Test Student", user_email, "pbkdf2_hash_mock")
        
    print(f"Test user resolved: ID {user_id}")
    
    # 2. Test Behavior Logging
    # Simulate a Software Engineer Aspirant interaction history
    db.clear_user_interactions(user_id)
    
    # Watched Quick Sort visual fully, liked & saved (Advanced)
    db.log_interaction(user_id, "R007", 98.0, True, True, True, True)
    # Watched Gemini context window fully (Intermediate)
    db.log_interaction(user_id, "R003", 92.0, True, True, False, False)
    # Watched MacBook vs Snapdragon fully (Intermediate)
    db.log_interaction(user_id, "R004", 85.0, True, False, False, False)
    # Skipped clickbait frontend roadmap course (Beginner)
    db.log_interaction(user_id, "R002", 15.0, False, False, False, False)

    print("Interactions logged. Running behavior analyzer...")
    analyzer = BehaviorAnalyzer(db)
    summary = analyzer.analyze_user_behavior(user_id)
    
    print("\n--- BEHAVIOR ANALYSIS SUMMARY ---")
    print(f"Interaction Count: {summary['interaction_count']}")
    print(f"Preferred Difficulty: {summary['preferred_difficulty']}")
    print(f"Average Watch Completion: {summary['watch_stats']['average_watch_percentage']}%")
    print(f"Category Scores: {summary['category_scores']}")
    print(f"Topic Scores: {summary['topic_scores']}")
    
    assert summary['interaction_count'] == 4, "Incorrect interaction count logged!"
    assert summary['preferred_difficulty'] in ['Advanced', 'Intermediate'], "Difficulty inference failure!"
    
    # 3. Test Hype Detector
    hype_detector = HypeDetector()
    clickbait_title = "Become a Frontend Dev in 7 Days and Land a 100k Job!"
    clickbait_transcript = "Stop wasting time at college! Learn everything in 24 hours and make 10k a month!"
    hype_score = hype_detector.detect_hype(clickbait_title, clickbait_transcript)
    print(f"\nHype score for '{clickbait_title}': {hype_score}")
    assert hype_score > 0.8, "Hype detector failed to flag clickbait!"

    # 4. Test Recommendation Scoring & Clickbait Penalty
    ai_service = AiService()
    rec_engine = RecommendationEngine(db, analyzer, ai_service, hype_detector)
    
    # Seed interest profile matching behavior summary
    db.update_user_interest_profile(
        user_id,
        "Software Engineering",
        ["Programming", "DSA"],
        {"Software Engineering": 0.95, "Programming": 0.85, "DSA": 0.90},
        "Simulated software engineering student profile.",
        "High"
    )
    
    print("\nGenerating recommendations...")
    selected_rec, rejected = rec_engine.generate_recommendations(user_id)
    
    print("\n--- SELECTED RECOMMENDATION ---")
    print(f"Title: {selected_rec['title']}")
    print(f"Category: {selected_rec['category']}")
    print(f"Relevance Score: {selected_rec['scores']['final_score']}")
    print(f"AI Reason: {selected_rec['reason']}")
    
    assert selected_rec['category'] == 'DSA' or selected_rec['category'] == 'Java', "Recommendation alignment failure!"
    
    print("\n--- REJECTED / CLICKBAIT CANDIDATES ---")
    for rc in rejected:
        print(f"Title: {rc['reel']['title']} | Hype: {rc['scores']['hype_score']} | Score: {rc['scores']['final_score']} | Reason: {rc['rejection_reason']}")
        
    # Check that REC_HYPE_01 (10 AI Tools) was rejected due to clickbait
    hype_rejected = [rc for rc in rejected if rc['reel']['id'] == 'REC_HYPE_01']
    assert len(hype_rejected) > 0, "Clickbait candidate was not rejected!"
    assert "Hype" in hype_rejected[0]['rejection_reason'] or "clickbait" in hype_rejected[0]['rejection_reason'], "Incorrect rejection reason for clickbait!"

    print("\nALL SCORING & PIPELINE TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
