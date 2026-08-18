import os
import json
import sqlite3
from datetime import datetime
from config import Config

# Try to import pymongo; it was installed but wrap in try-except for absolute robustness
try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

class DbService:
    def __init__(self):
        self.use_mongo = False
        self.mongo_client = None
        self.mongo_db = None
        
        # Determine whether to use MongoDB or SQLite
        if MONGO_AVAILABLE and Config.MONGO_URI:
            try:
                # We set a short timeout so it doesn't hang if Atlas is unreachable
                self.mongo_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
                # Check connection
                self.mongo_client.server_info()
                # Use database name from URI or default to "reel_recommendation"
                db_name = Config.MONGO_URI.split('/')[-1].split('?')[0]
                if not db_name:
                    db_name = "reel_recommendation"
                self.mongo_db = self.mongo_client[db_name]
                self.use_mongo = True
                print(f"Connected to MongoDB Atlas database: {db_name}")
            except Exception as e:
                print(f"Failed to connect to MongoDB Atlas ({e}). Falling back to SQLite.")
                self.use_mongo = False
        
        if not self.use_mongo:
            # Setup SQLite
            self.sqlite_db_path = Config.SQLITE_DB_PATH
            # Ensure instance directory exists
            os.makedirs(os.path.dirname(self.sqlite_db_path), exist_ok=True)
            print(f"Using SQLite database at: {self.sqlite_db_path}")

    def get_connection(self):
        """Get a direct connection to SQLite. Only used for SQLite mode."""
        if self.use_mongo:
            return None
        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create tables/collections and seed initial data if empty."""
        if self.use_mongo:
            # In MongoDB, collections are created implicitly.
            # We check if 'reels' collection is empty to decide if we need to seed.
            reels_count = self.mongo_db['reels'].count_documents({})
            if reels_count == 0:
                self._seed_data()
        else:
            # Initialize SQLite schema
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Reels table (both fictional reels and educational target recommendations)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reels (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                transcript TEXT,
                category TEXT NOT NULL,
                creator_type TEXT,
                duration INTEGER,
                topics TEXT, -- JSON array of strings
                difficulty TEXT,
                quality_score REAL,
                hype_score REAL,
                is_recommendation_only INTEGER DEFAULT 0
            )
            ''')
            
            # Interactions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reel_id TEXT NOT NULL,
                watch_percentage REAL NOT NULL,
                liked INTEGER NOT NULL,
                saved INTEGER NOT NULL,
                shared INTEGER NOT NULL,
                rewatched INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (reel_id) REFERENCES reels(id)
            )
            ''')
            
            # Interest Profiles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS interest_profiles (
                user_id INTEGER PRIMARY KEY,
                primary_interest TEXT NOT NULL,
                secondary_interests TEXT, -- JSON array of strings
                interest_scores TEXT, -- JSON object mapping string to score
                reasoning TEXT,
                confidence TEXT,
                evolution_signal TEXT DEFAULT 'stable',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Recommendations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reference_reel_id TEXT,
                recommended_reel_id TEXT NOT NULL,
                category TEXT NOT NULL,
                reason TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                confidence TEXT NOT NULL,
                relevance_score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (recommended_reel_id) REFERENCES reels(id)
            )
            ''')
            
            # Feedback table (👍/👎/🔖/🚫 on recommendations)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recommendation_id INTEGER,
                reel_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Interest Evolution snapshots (daily profile snapshots)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS interest_evolution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                primary_interest TEXT NOT NULL,
                interest_scores TEXT NOT NULL,
                evolution_signal TEXT DEFAULT 'stable',
                snapshot_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            conn.commit()
            
            # Migration: add evolution_signal column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE interest_profiles ADD COLUMN evolution_signal TEXT DEFAULT 'stable'")
                conn.commit()
            except Exception:
                pass  # column already exists
            
            # Check if reels table is empty to seed
            cursor.execute("SELECT COUNT(*) FROM reels")
            if cursor.fetchone()[0] == 0:
                self._seed_data()
                
            conn.close()

    def _seed_data(self):
        """Seed default reels and recommendation candidates."""
        # 8 interactive fictional Reels
        interactive_reels = [
            {
                "id": "R001",
                "title": "When Java finally works after 3 hours",
                "description": "A programmer struggling with a Java compilation bug.",
                "transcript": "Every developer knows this feeling: you delete one semicolon, and the whole system crashes. But when it compiles... oh, the sweet dopamine hit!",
                "category": "Java",
                "creator_type": "Dev Lifestyle",
                "duration": 35,
                "topics": ["Java", "Programming", "Debugging", "Developer Humor"],
                "difficulty": "Beginner",
                "quality_score": 0.6,
                "hype_score": 0.2,
                "is_recommendation_only": False
            },
            {
                "id": "R002",
                "title": "Become a Frontend Dev in 7 Days and Land a 100k Job!",
                "description": "No experience needed. Just follow this secret roadmap.",
                "transcript": "Stop wasting time at college! In just 7 days, you can master React, Next.js, and Tailwind, and secure a six-figure remote job. Click link in bio for my course!",
                "category": "Web Development",
                "creator_type": "Clickbait Guru",
                "duration": 45,
                "topics": ["Web Development", "Career", "React", "HTML/CSS"],
                "difficulty": "Beginner",
                "quality_score": 0.2,
                "hype_score": 0.95,
                "is_recommendation_only": False
            },
            {
                "id": "R003",
                "title": "Gemini 1.5 Pro Context Window is Insane",
                "description": "Exploring the 2 million token limit.",
                "transcript": "This new AI model can ingest entire codebases, audio files, and books in one prompt. Here is how developers are using the long context window to refactor old legacy code...",
                "category": "AI",
                "creator_type": "Tech Edu",
                "duration": 58,
                "topics": ["AI", "Machine Learning", "LLMs", "Developer Tools"],
                "difficulty": "Intermediate",
                "quality_score": 0.9,
                "hype_score": 0.3,
                "is_recommendation_only": False
            },
            {
                "id": "R004",
                "title": "MacBook Pro M3 Max vs Snapdragon X Elite",
                "description": "Which laptop is best for coding and developer workflows?",
                "transcript": "Today we are benchmarking the M3 Max against the new Snapdragon X Elite for compiler speeds, Docker runtimes, and battery life. Let's look at the thermal throttling under load...",
                "category": "Hardware",
                "creator_type": "Independent",
                "duration": 60,
                "topics": ["Hardware", "Laptops", "Developer Setup", "Benchmarks"],
                "difficulty": "Intermediate",
                "quality_score": 0.85,
                "hype_score": 0.2,
                "is_recommendation_only": False
            },
            {
                "id": "R005",
                "title": "A Day in the Life of a Silicon Valley Software Engineer",
                "description": "Office tour, free food, and coding at a big tech company.",
                "transcript": "Waking up at 7 AM, grabbing a free matcha latte at the tech bar, attending a quick standup meeting, writing 10 lines of code, and then eating gourmet lunch...",
                "category": "Career",
                "creator_type": "Dev Lifestyle",
                "duration": 40,
                "topics": ["Career", "Software Engineering", "Developer Lifestyle", "Big Tech"],
                "difficulty": "Beginner",
                "quality_score": 0.7,
                "hype_score": 0.4,
                "is_recommendation_only": False
            },
            {
                "id": "R006",
                "title": "How SQL Injection works in 60 seconds",
                "description": "A live demonstration of vulnerability exploitation.",
                "transcript": "Ever wondered how hackers steal database info? Here is a form. When we type a single quote followed by OR 1=1 -- we bypass the authentication check entirely...",
                "category": "Cybersecurity",
                "creator_type": "Tech Edu",
                "duration": 59,
                "topics": ["Cybersecurity", "Databases", "Web Security", "SQL Injection"],
                "difficulty": "Intermediate",
                "quality_score": 0.95,
                "hype_score": 0.1,
                "is_recommendation_only": False
            },
            {
                "id": "R007",
                "title": "Visualizing Quick Sort in your head",
                "description": "Divide and conquer algorithm animation.",
                "transcript": "Let's choose a pivot. Elements smaller go left, larger go right. Repeat recursively. This pivot mechanism gives Quick Sort an average case time complexity of O(N log N)...",
                "category": "DSA",
                "creator_type": "Tech Edu",
                "duration": 50,
                "topics": ["DSA", "Algorithms", "Sorting", "Interview Prep"],
                "difficulty": "Advanced",
                "quality_score": 0.9,
                "hype_score": 0.1,
                "is_recommendation_only": False
            },
            {
                "id": "R008",
                "title": "AWS is DEAD! Use this AI cloud for free forever!",
                "description": "Why Amazon is shaking in its boots.",
                "transcript": "AWS is charging you too much. This new AI cloud provider lets you deploy unlimited microservices and databases without putting in a credit card! Get started before they block it...",
                "category": "Cloud Computing",
                "creator_type": "Clickbait Guru",
                "duration": 30,
                "topics": ["Cloud Computing", "AWS", "DevOps", "AI Cloud"],
                "difficulty": "Beginner",
                "quality_score": 0.3,
                "hype_score": 0.9,
                "is_recommendation_only": False
            }
        ]
        
        # 8 candidate Recommendations (High quality educational resources, plus a couple of clickbait ones to test filtering)
        rec_reels = [
            {
                "id": "REC_DSA_01",
                "title": "How Data Structures Are Used in Real Software Projects",
                "description": "Under the hood of database indexes, router tables, and undo buffers.",
                "category": "DSA",
                "creator_type": "Tech Edu",
                "duration": 180,
                "topics": ["DSA", "Algorithms", "Software Engineering", "System Design"],
                "difficulty": "Intermediate",
                "quality_score": 0.95,
                "hype_score": 0.15,
                "is_recommendation_only": True
            },
            {
                "id": "REC_AI_01",
                "title": "How LLMs Are Used in Modern Applications",
                "description": "Building production RAG pipelines with vector databases.",
                "category": "AI",
                "creator_type": "Tech Edu",
                "duration": 210,
                "topics": ["AI", "Machine Learning", "Vector DBs", "RAG"],
                "difficulty": "Advanced",
                "quality_score": 0.9,
                "hype_score": 0.2,
                "is_recommendation_only": True
            },
            {
                "id": "REC_SEC_01",
                "title": "Understanding JWT Security: Best Practices",
                "description": "How to prevent token stealing and signature bypass.",
                "category": "Cybersecurity",
                "creator_type": "Tech Edu",
                "duration": 150,
                "topics": ["Cybersecurity", "Web Security", "JWT", "Authentication"],
                "difficulty": "Intermediate",
                "quality_score": 0.88,
                "hype_score": 0.1,
                "is_recommendation_only": True
            },
            {
                "id": "REC_HW_01",
                "title": "System Architecture of Modern CPU Architectures (x86 vs ARM)",
                "description": "Why ARM dominates power efficiency in cloud and mobile computing.",
                "category": "Hardware",
                "creator_type": "Tech Edu",
                "duration": 240,
                "topics": ["Hardware", "ARM", "CPU Architecture", "Performance"],
                "difficulty": "Advanced",
                "quality_score": 0.92,
                "hype_score": 0.1,
                "is_recommendation_only": True
            },
            {
                "id": "REC_CLD_01",
                "title": "Designing a Scalable CI/CD Pipeline on Google Cloud",
                "description": "Using Cloud Build, Artifact Registry, and Cloud Run.",
                "category": "Cloud Computing",
                "creator_type": "Tech Edu",
                "duration": 190,
                "topics": ["Cloud Computing", "DevOps", "CI/CD", "Google Cloud"],
                "difficulty": "Intermediate",
                "quality_score": 0.9,
                "hype_score": 0.15,
                "is_recommendation_only": True
            },
            {
                "id": "REC_WEB_01",
                "title": "Under the Hood of React Server Components",
                "description": "How streaming renders HTML and hydrates client components.",
                "category": "Web Development",
                "creator_type": "Tech Edu",
                "duration": 160,
                "topics": ["Web Development", "React", "Frontend", "Performance"],
                "difficulty": "Intermediate",
                "quality_score": 0.88,
                "hype_score": 0.2,
                "is_recommendation_only": True
            },
            {
                "id": "REC_JAVA_01",
                "title": "Garbage Collection Tuning in High-Throughput Java Applications",
                "description": "Analyzing JVM memory heap settings and G1 GC performance.",
                "category": "Java",
                "creator_type": "Tech Edu",
                "duration": 220,
                "topics": ["Java", "JVM", "Performance Tuning", "OOP"],
                "difficulty": "Advanced",
                "quality_score": 0.95,
                "hype_score": 0.1,
                "is_recommendation_only": True
            },
            {
                "id": "REC_HYPE_01",
                "title": "10 AI Tools That Will Get You a Job Instantly! (No Skills Required)",
                "description": "Make 10k a month copy pasting with AI.",
                "category": "AI",
                "creator_type": "Clickbait Guru",
                "duration": 120,
                "topics": ["AI", "Career", "No Code", "Automation"],
                "difficulty": "Beginner",
                "quality_score": 0.3,
                "hype_score": 0.98,
                "is_recommendation_only": True
            }
        ]
        
        all_reels = interactive_reels + rec_reels
        
        if self.use_mongo:
            self.mongo_db['reels'].insert_many(all_reels)
            print("Seeded reels in MongoDB.")
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            for r in all_reels:
                cursor.execute(
                    "INSERT INTO reels (id, title, description, transcript, category, creator_type, duration, topics, difficulty, quality_score, hype_score, is_recommendation_only) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        r["id"], r["title"], r.get("description", ""), r.get("transcript", ""), r["category"],
                        r.get("creator_type", "Independent"), r.get("duration", 60), json.dumps(r["topics"]), r.get("difficulty", "Beginner"),
                        r.get("quality_score", 0.5), r.get("hype_score", 0.1), 1 if r.get("is_recommendation_only", False) else 0
                    )
                )
            conn.commit()
            conn.close()
            print("Seeded reels in SQLite.")

    # --- User functions ---
    def get_user_by_email(self, email):
        if self.use_mongo:
            user = self.mongo_db['users'].find_one({"email": email})
            if user:
                user['id'] = str(user['_id'])
            return user
        else:
            conn = self.get_connection()
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()
            return dict(row) if row else None

    def create_user(self, name, email, password_hash):
        if self.use_mongo:
            user_data = {
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "created_at": datetime.utcnow()
            }
            res = self.mongo_db['users'].insert_one(user_data)
            return str(res.inserted_id)
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id

    # --- Reels functions ---
    def get_all_reels(self):
        if self.use_mongo:
            reels = list(self.mongo_db['reels'].find({"is_recommendation_only": False}))
            for r in reels:
                r['id'] = r.get('id', str(r['_id']))
            return reels
        else:
            conn = self.get_connection()
            rows = conn.execute("SELECT * FROM reels WHERE is_recommendation_only = 0").fetchall()
            conn.close()
            results = []
            for row in rows:
                r = dict(row)
                r['topics'] = json.loads(r['topics'])
                r['is_recommendation_only'] = False
                results.append(r)
            return results

    def get_all_recommendation_reels(self):
        if self.use_mongo:
            reels = list(self.mongo_db['reels'].find({"is_recommendation_only": True}))
            for r in reels:
                r['id'] = r.get('id', str(r['_id']))
            return reels
        else:
            conn = self.get_connection()
            rows = conn.execute("SELECT * FROM reels WHERE is_recommendation_only = 1").fetchall()
            conn.close()
            results = []
            for row in rows:
                r = dict(row)
                r['topics'] = json.loads(r['topics'])
                r['is_recommendation_only'] = True
                results.append(r)
            return results

    def get_reel_by_id(self, reel_id):
        if self.use_mongo:
            r = self.mongo_db['reels'].find_one({"id": reel_id})
            if not r:
                r = self.mongo_db['reels'].find_one({"_id": ObjectId(reel_id) if len(reel_id) == 24 else None})
            if r:
                r['id'] = r.get('id', str(r['_id']))
            return r
        else:
            conn = self.get_connection()
            row = conn.execute("SELECT * FROM reels WHERE id = ?", (reel_id,)).fetchone()
            conn.close()
            if row:
                r = dict(row)
                r['topics'] = json.loads(r['topics'])
                r['is_recommendation_only'] = bool(r['is_recommendation_only'])
                return r
            return None

    # --- Interactions functions ---
    def log_interaction(self, user_id, reel_id, watch_percentage, liked, saved, shared, rewatched):
        if self.use_mongo:
            # Keep log of all interactions
            interaction = {
                "user_id": str(user_id),
                "reel_id": reel_id,
                "watch_percentage": float(watch_percentage),
                "liked": bool(liked),
                "saved": bool(saved),
                "shared": bool(shared),
                "rewatched": bool(rewatched),
                "timestamp": datetime.utcnow()
            }
            res = self.mongo_db['interactions'].insert_one(interaction)
            return str(res.inserted_id)
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interactions (user_id, reel_id, watch_percentage, liked, saved, shared, rewatched) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id, reel_id, float(watch_percentage),
                    1 if liked else 0, 1 if saved else 0, 1 if shared else 0, 1 if rewatched else 0
                )
            )
            int_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return int_id

    def get_user_interactions(self, user_id):
        if self.use_mongo:
            ints = list(self.mongo_db['interactions'].find({"user_id": str(user_id)}).sort("timestamp", -1))
            for i in ints:
                i['id'] = str(i['_id'])
            return ints
        else:
            conn = self.get_connection()
            rows = conn.execute("SELECT * FROM interactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def clear_user_interactions(self, user_id):
        """Reset interactions for profiling test."""
        if self.use_mongo:
            self.mongo_db['interactions'].delete_many({"user_id": str(user_id)})
            self.mongo_db['interest_profiles'].delete_one({"user_id": str(user_id)})
            self.mongo_db['recommendations'].delete_many({"user_id": str(user_id)})
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM interactions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM interest_profiles WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM recommendations WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()

    # --- Interest Profile functions ---
    def get_user_interest_profile(self, user_id):
        if self.use_mongo:
            prof = self.mongo_db['interest_profiles'].find_one({"user_id": str(user_id)})
            if prof:
                prof['id'] = str(prof['_id'])
            return prof
        else:
            conn = self.get_connection()
            row = conn.execute("SELECT * FROM interest_profiles WHERE user_id = ?", (user_id,)).fetchone()
            conn.close()
            if row:
                prof = dict(row)
                prof['secondary_interests'] = json.loads(prof['secondary_interests'])
                prof['interest_scores'] = json.loads(prof['interest_scores'])
                prof.setdefault('evolution_signal', 'stable')
                return prof
            return None

    def update_user_interest_profile(self, user_id, primary_interest, secondary_interests,
                                      interest_scores, reasoning, confidence, evolution_signal='stable'):
        if self.use_mongo:
            filter_dict = {"user_id": str(user_id)}
            update_dict = {
                "$set": {
                    "primary_interest": primary_interest,
                    "secondary_interests": list(secondary_interests),
                    "interest_scores": dict(interest_scores),
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "evolution_signal": evolution_signal,
                    "updated_at": datetime.utcnow()
                }
            }
            self.mongo_db['interest_profiles'].update_one(filter_dict, update_dict, upsert=True)
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interest_profiles (user_id, primary_interest, secondary_interests, interest_scores, reasoning, confidence, evolution_signal, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(user_id) DO UPDATE SET "
                "primary_interest=excluded.primary_interest, "
                "secondary_interests=excluded.secondary_interests, "
                "interest_scores=excluded.interest_scores, "
                "reasoning=excluded.reasoning, "
                "confidence=excluded.confidence, "
                "evolution_signal=excluded.evolution_signal, "
                "updated_at=CURRENT_TIMESTAMP",
                (
                    user_id, primary_interest,
                    json.dumps(list(secondary_interests)),
                    json.dumps(dict(interest_scores)),
                    reasoning, confidence, evolution_signal
                )
            )
            conn.commit()
            conn.close()

    # --- Recommendations functions ---
    def save_recommendation(self, user_id, reference_reel_id, recommended_reel_id, category, reason, difficulty, confidence, relevance_score):
        if self.use_mongo:
            rec = {
                "user_id": str(user_id),
                "reference_reel_id": reference_reel_id,
                "recommended_reel_id": recommended_reel_id,
                "category": category,
                "reason": reason,
                "difficulty": difficulty,
                "confidence": confidence,
                "relevance_score": float(relevance_score),
                "created_at": datetime.utcnow()
            }
            res = self.mongo_db['recommendations'].insert_one(rec)
            return str(res.inserted_id)
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO recommendations (user_id, reference_reel_id, recommended_reel_id, category, reason, difficulty, confidence, relevance_score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id, reference_reel_id, recommended_reel_id, category,
                    reason, difficulty, confidence, float(relevance_score)
                )
            )
            rec_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return rec_id

    def get_user_recommendations(self, user_id):
        if self.use_mongo:
            recs = list(self.mongo_db['recommendations'].find({"user_id": str(user_id)}).sort("created_at", -1))
            for r in recs:
                r['id'] = str(r['_id'])
            return recs
        else:
            conn = self.get_connection()
            rows = conn.execute("SELECT * FROM recommendations WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
            conn.close()
            return [dict(row) for row in rows]

    # --- Feedback functions ---
    def log_feedback(self, user_id, reel_id, feedback_type, recommendation_id=None):
        if self.use_mongo:
            self.mongo_db['feedback'].insert_one({
                "user_id": str(user_id), "reel_id": reel_id,
                "feedback_type": feedback_type, "recommendation_id": recommendation_id,
                "created_at": datetime.utcnow()
            })
        else:
            conn = self.get_connection()
            conn.execute(
                "INSERT INTO feedback (user_id, reel_id, feedback_type, recommendation_id) VALUES (?, ?, ?, ?)",
                (user_id, reel_id, feedback_type, recommendation_id)
            )
            conn.commit()
            conn.close()

    def get_disliked_categories(self, user_id):
        """Returns categories the user marked not_interested or not_useful."""
        feedback = self.get_user_feedback(user_id)
        disliked = set()
        for f in feedback:
            if f['feedback_type'] in ('not_interested', 'not_useful'):
                reel = self.get_reel_by_id(f['reel_id'])
                if reel:
                    disliked.add(reel['category'])
        return disliked

    def get_user_feedback(self, user_id):
        if self.use_mongo:
            return list(self.mongo_db['feedback'].find({"user_id": str(user_id)}).sort("created_at", -1))
        else:
            conn = self.get_connection()
            rows = conn.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
            conn.close()
            return [dict(r) for r in rows]

    # --- Interest Evolution snapshots ---
    def save_evolution_snapshot(self, user_id, primary_interest, interest_scores, evolution_signal='stable'):
        from datetime import date
        today = date.today().isoformat()
        if self.use_mongo:
            self.mongo_db['interest_evolution'].update_one(
                {"user_id": str(user_id), "snapshot_date": today},
                {"$set": {"primary_interest": primary_interest,
                           "interest_scores": interest_scores,
                           "evolution_signal": evolution_signal}},
                upsert=True
            )
        else:
            conn = self.get_connection()
            cursor = conn.cursor()
            existing = cursor.execute(
                "SELECT id FROM interest_evolution WHERE user_id=? AND snapshot_date=?",
                (user_id, today)
            ).fetchone()
            if existing:
                cursor.execute(
                    "UPDATE interest_evolution SET primary_interest=?, interest_scores=?, evolution_signal=? WHERE user_id=? AND snapshot_date=?",
                    (primary_interest, json.dumps(interest_scores), evolution_signal, user_id, today)
                )
            else:
                cursor.execute(
                    "INSERT INTO interest_evolution (user_id, primary_interest, interest_scores, evolution_signal, snapshot_date) VALUES (?,?,?,?,?)",
                    (user_id, primary_interest, json.dumps(interest_scores), evolution_signal, today)
                )
            conn.commit()
            conn.close()

    def get_evolution_history(self, user_id, limit=7):
        """Oldest-first snapshots for timeline charting."""
        if self.use_mongo:
            snaps = list(self.mongo_db['interest_evolution'].find(
                {"user_id": str(user_id)}
            ).sort("snapshot_date", -1).limit(limit))
            snaps.reverse()
            return snaps
        else:
            conn = self.get_connection()
            rows = conn.execute(
                "SELECT * FROM interest_evolution WHERE user_id=? ORDER BY snapshot_date DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            conn.close()
            result = [dict(r) for r in rows]
            result.reverse()
            for r in result:
                r['interest_scores'] = json.loads(r['interest_scores'])
            return result
