#!/usr/bin/env python3
"""
Test data generator for Kryptopedia

This script adds sample test data to the Kryptopedia database for development purposes.
It creates:
1. Multiple users with different roles
2. Several articles on various topics
3. Revisions for those articles
4. Proposals for edits
5. Rewards for contributions

Usage: python add-test-data.py
"""

import os
import sys
import asyncio
import random
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection info from environment or use defaults
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "kryptopedia")

# Sample users (in addition to admin)
TEST_USERS = [
    {
        "username": "editor1",
        "email": "editor1@example.com",
        "password": "password123",
        "role": "editor"
    },
    {
        "username": "editor2",
        "email": "editor2@example.com",
        "password": "password123",
        "role": "editor"
    },
    {
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123",
        "role": "user"
    },
    {
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123",
        "role": "user"
    },
    {
        "username": "user3",
        "email": "user3@example.com",
        "password": "password123",
        "role": "user"
    }
]

# Sample articles
TEST_ARTICLES = [
    {
        "title": "Introduction to Cryptography",
        "content": """
<h1>Introduction to Cryptography</h1>

<p>Cryptography is the practice and study of techniques for secure communication in the presence of third parties. It involves creating and analyzing protocols that prevent third parties or the public from reading private messages.</p>

<h2>History of Cryptography</h2>

<p>The history of cryptography began thousands of years ago. Cryptography has roots in various aspects of mathematics and computer science. Modern cryptography exists at the intersection of the disciplines of mathematics, computer science, electrical engineering, communication science, and physics.</p>

<h2>Types of Cryptography</h2>

<h3>Symmetric Key Cryptography</h3>
<p>Symmetric-key algorithms use the same cryptographic keys for both the encryption and decryption process. The keys may be identical or there may be a simple transformation to go between the two keys. This requirement that both parties have access to the secret key is one of the main drawbacks of symmetric key encryption.</p>

<h3>Public Key Cryptography</h3>
<p>Public-key cryptography, or asymmetric cryptography, is a cryptographic system that uses pairs of keys. Each pair consists of a public key (which may be known to others) and a private key (which is only known to the owner). The generation of such key pairs depends on cryptographic algorithms which are based on mathematical problems termed one-way functions.</p>

<h3>Hash Functions</h3>
<p>A cryptographic hash function is a special class of hash function that has certain properties which make it suitable for use in cryptography. It is a mathematical algorithm that maps data of arbitrary size to a bit string of a fixed size (a hash) and is designed to be a one-way function, that is, a function which is infeasible to invert.</p>
        """,
        "summary": "An overview of cryptography principles, history, and types",
        "categories": ["Security", "Cryptography"],
        "tags": ["encryption", "security", "algorithms"],
        "metadata": {
            "hasAudio": False,
            "hasSpecialSymbols": False,
            "containsMadeUpContent": False
        }
    },
    {
        "title": "Blockchain Technology",
        "content": """
<h1>Blockchain Technology</h1>

<p>A blockchain is a growing list of records, called blocks, that are linked using cryptography. Each block contains a cryptographic hash of the previous block, a timestamp, and transaction data. By design, a blockchain is resistant to modification of its data.</p>

<h2>How Blockchain Works</h2>

<p>Blockchain is a decentralized, distributed ledger technology that records the provenance of a digital asset. By inherent design, the data on a blockchain cannot be modified, which makes it a legitimate disruptor for industries like payments, cybersecurity and healthcare.</p>

<h2>Key Components</h2>

<h3>Blocks</h3>
<p>Blocks hold batches of valid transactions that are hashed and encoded into a Merkle tree. Each block includes the cryptographic hash of the prior block in the blockchain, linking the two. This iterative process confirms the integrity of the previous block, all the way back to the initial block, which is known as the genesis block.</p>

<h3>Mining</h3>
<p>Mining is the process by which new blocks are created, and transactions are confirmed. Miners use special software to solve mathematical algorithms that reward newly created cryptocurrency. This process also secures the network from fraudulent activities.</p>

<h3>Consensus Mechanisms</h3>
<p>A consensus mechanism is a fault-tolerant mechanism that is used in blockchain systems to achieve the necessary agreement on a single data value or a single state of the network among distributed processes or multi-agent systems. Popular consensus mechanisms include Proof of Work (PoW), Proof of Stake (PoS), and Delegated Proof of Stake (DPoS).</p>
        """,
        "summary": "An introduction to blockchain technology and its key components",
        "categories": ["Technology", "Blockchain"],
        "tags": ["blockchain", "cryptocurrency", "distributed-ledger"],
        "metadata": {
            "hasAudio": False,
            "hasSpecialSymbols": False,
            "containsMadeUpContent": False
        }
    },
    {
        "title": "Quantum Computing Basics",
        "content": """
<h1>Quantum Computing Basics</h1>

<p>Quantum computing is an area of computing focused on developing computer technology based on the principles of quantum theory. Quantum computers use quantum bits or qubits instead of traditional binary bits to perform computations.</p>

<h2>Quantum vs. Classical Computing</h2>

<p>Classical computers encode information in bits, with each bit representing either a 1 or a 0. Quantum computers use quantum bits or qubits, which can represent both 1 and 0 simultaneously through a quantum mechanical property called superposition.</p>

<h2>Key Quantum Concepts</h2>

<h3>Superposition</h3>
<p>Superposition is a principle of quantum mechanics that describes a quantum system's ability to exist in multiple states simultaneously until it is measured. This allows quantum computers to process a vast number of possibilities at once.</p>

<h3>Entanglement</h3>
<p>Quantum entanglement is a physical phenomenon that occurs when a pair or group of particles interact in such a way that the quantum state of each particle cannot be described independently of the state of the others. This allows for quantum teleportation and is a key resource for quantum computing.</p>

<h3>Quantum Gates</h3>
<p>Quantum gates are the basic quantum circuit operating on a small number of qubits. They are the building blocks of quantum circuits, like classical logic gates are for conventional digital circuits. The most common gates operate on spaces of one or two qubits.</p>

<h2>Quantum Algorithms</h2>

<p>Quantum algorithms are designed to run on a realistic model of quantum computation, the most commonly used model being the quantum circuit model. Notable quantum algorithms include Shor's algorithm for factoring and Grover's algorithm for searching an unsorted database.</p>
        """,
        "summary": "An introduction to quantum computing principles and terminology",
        "categories": ["Technology", "Quantum Computing"],
        "tags": ["quantum", "computing", "physics"],
        "metadata": {
            "hasAudio": False,
            "hasSpecialSymbols": True,
            "containsMadeUpContent": False
        }
    },
    {
        "title": "Digital Privacy Guide",
        "content": """
<h1>Digital Privacy Guide</h1>

<p>Digital privacy refers to the protection of personal information shared online. As our lives become increasingly digital, understanding and managing privacy online is crucial.</p>

<h2>Threats to Digital Privacy</h2>

<p>There are numerous threats to digital privacy, including data breaches, surveillance, tracking by advertisers, and identity theft. Understanding these threats is the first step in protecting your privacy online.</p>

<h2>Protection Strategies</h2>

<h3>Use Strong Passwords</h3>
<p>Strong passwords are your first line of defense against unauthorized access to your accounts. Use long, complex passwords with a mix of characters, and use different passwords for different accounts. A password manager can help you create and manage strong passwords.</p>

<h3>Enable Two-Factor Authentication</h3>
<p>Two-factor authentication adds an extra layer of security by requiring something you know (password) and something you have (like a phone). Enable this feature on all accounts that support it.</p>

<h3>Be Careful What You Share</h3>
<p>Think twice before posting personal information online. Once information is online, it can be difficult to remove it completely. Be particularly careful with personal identifiers like your address, phone number, and financial information.</p>

<h3>Use Privacy-Focused Tools</h3>
<p>Consider using privacy-focused tools like VPNs, secure messaging apps, and privacy-respecting search engines. These tools can help protect your data from tracking and surveillance.</p>

<h2>Privacy Laws and Regulations</h2>

<p>Various laws and regulations protect digital privacy, such as the General Data Protection Regulation (GDPR) in Europe and the California Consumer Privacy Act (CCPA) in the United States. Understanding your rights under these laws can help you protect your data.</p>
        """,
        "summary": "A guide to understanding and protecting your privacy in the digital age",
        "categories": ["Security", "Privacy"],
        "tags": ["privacy", "security", "online-safety"],
        "metadata": {
            "hasAudio": False,
            "hasSpecialSymbols": False,
            "containsMadeUpContent": False
        }
    },
    {
        "title": "Artificial Intelligence Overview",
        "content": """
<h1>Artificial Intelligence Overview</h1>

<p>Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.</p>

<h2>Types of AI</h2>

<h3>Narrow AI</h3>
<p>Narrow AI, also known as Weak AI, is designed to perform a narrow task such as voice recognition or driving a car. Most AI systems today are narrow AI systems that focus on performing specific tasks.</p>

<h3>General AI</h3>
<p>General AI, also known as Strong AI, refers to machines that possess the ability to perform any intellectual task that a human being can. This type of AI does not currently exist and is a subject of research and speculation.</p>

<h3>Superintelligent AI</h3>
<p>Superintelligent AI surpasses human intelligence across all fields including creativity, social intelligence, and general wisdom. Developing superintelligent AI raises important ethical questions and potential risks.</p>

<h2>AI Techniques</h2>

<h3>Machine Learning</h3>
<p>Machine Learning is a subset of AI that focuses on enabling systems to learn from data and improve from experience without being explicitly programmed. It involves algorithms that parse data, learn from that data, and then apply that learning to make informed decisions.</p>

<h3>Neural Networks</h3>
<p>Neural Networks are computing systems inspired by the biological neural networks that constitute animal brains. These systems "learn" to perform tasks by considering examples, generally without being programmed with task-specific rules.</p>

<h3>Deep Learning</h3>
<p>Deep Learning is a subset of machine learning that uses neural networks with many layers (thus "deep"). These networks can learn complex patterns in large amounts of data. Deep learning has driven many recent advances in AI, including speech recognition and computer vision.</p>

<h2>Applications of AI</h2>

<p>AI is being applied across various fields including healthcare, finance, transportation, and entertainment. Applications include medical diagnosis, fraud detection, autonomous vehicles, and personalized content recommendations.</p>
        """,
        "summary": "An overview of artificial intelligence, its types, techniques, and applications",
        "categories": ["Technology", "Artificial Intelligence"],
        "tags": ["AI", "machine-learning", "neural-networks"],
        "metadata": {
            "hasAudio": False,
            "hasSpecialSymbols": False,
            "containsMadeUpContent": False
        }
    }
]

# Sample revisions/proposals
SAMPLE_REVISIONS = [
    "Added more detailed information about the history.",
    "Fixed some grammatical errors and improved readability.",
    "Updated with recent developments in the field.",
    "Added a new section on practical applications.",
    "Included more examples to illustrate key concepts.",
    "Reorganized the content for better flow.",
    "Fixed technical inaccuracies in the description.",
    "Added references to recent research papers."
]

def generate_slug(title):
    """Generate a slug from a title"""
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().replace(" ", "-")
    # Remove special characters
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Add timestamp to ensure uniqueness
    slug = f"{slug}-{int(datetime.now().timestamp())}"
    return slug

async def add_test_data(mongo_uri, db_name):
    """Add test data to the database"""
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    # Store user IDs for later use
    user_ids = {}
    
    # Add test users
    for user_data in TEST_USERS:
        # Check if user already exists
        existing_user = await db["users"].find_one({"username": user_data["username"]})
        if not existing_user:
            # Hash password
            hashed_password = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt())
            
            # Prepare user document
            user_doc = {
                "username": user_data["username"],
                "email": user_data["email"],
                "passwordHash": hashed_password.decode('utf-8'),
                "role": user_data["role"],
                "joinDate": datetime.now(),
                "reputation": random.randint(0, 100),
                "contributions": {
                    "articlesCreated": 0,
                    "editsPerformed": 0,
                    "rewardsReceived": 0
                }
            }
            
            # Insert user
            result = await db["users"].insert_one(user_doc)
            user_ids[user_data["username"]] = result.inserted_id
            print(f"Created user: {user_data['username']}")
        else:
            user_ids[user_data["username"]] = existing_user["_id"]
            print(f"User already exists: {user_data['username']}")
    
    # Get admin user as well
    admin_user = await db["users"].find_one({"username": "admin"})
    if admin_user:
        user_ids["admin"] = admin_user["_id"]
    
    # Add test articles
    for article_data in TEST_ARTICLES:
        # Check if article already exists
        existing_article =
