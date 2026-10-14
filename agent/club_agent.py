import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class ClubAgent:
    """
    AI Agent for Student Club Information.
    Features:
    1. Built-in Offline Natural Language & Intent Matcher (requires zero API keys).
    2. Optional Gemini API plug-in layer for advanced generative answers.
    3. Strict grounding to club knowledge base: clearly informs users when information is unavailable.
    """

    def __init__(self, data_path: Optional[Path] = None, gemini_api_key: Optional[str] = None):
        self.data_path = data_path or Path(__file__).resolve().parent.parent / "data" / "clubs.json"
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
        self.clubs: List[Dict[str, Any]] = []
        self.clubs_by_id: Dict[str, Dict[str, Any]] = {}
        self.gemini_client = None
        self._load_data()
        self._init_gemini()

    def _load_data(self) -> None:
        """Loads club information from the JSON data file."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.clubs = json.load(f)
                self.clubs_by_id = {c["id"]: c for c in self.clubs}
        except Exception as e:
            print(f"[ClubAgent Error] Failed to load clubs data from {self.data_path}: {e}")
            self.clubs = []
            self.clubs_by_id = {}

    def _init_gemini(self) -> None:
        """Initializes Gemini API client if API key and library are present."""
        if not self.gemini_api_key:
            return

        try:
            # Check for modern google-genai or google-generativeai
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_client = genai.GenerativeModel(
                model_name="gemini-3.8-flash",
                system_instruction=(
                    "You are 'CampusClub AI', the official College Student Club Information Assistant. "
                    "You only have information regarding the 5 official student clubs provided in the knowledge base: "
                    "Coding Club, AI/ML Club, Robotics Club, Cultural Club, and Sports Club. "
                    "CRITICAL RULE: If a user asks about any club, event, campus service, exam, fee, or topic "
                    "that is not explicitly present in the provided knowledge base, you MUST clearly state: "
                    "'I'm sorry, but that information is not available in my club directory. Currently, I only have verified information for our official 5 clubs: Coding Club, AI/ML Club, Robotics Club, Cultural Club, and Sports Club. For other clubs or campus inquiries, please contact the Student Affairs Office (Email: studentaffairs@campus.edu, Room 101).' "
                    "Keep answers friendly, well-structured, formatted with markdown bullets, and college-student oriented."
                )
            )
            print("[ClubAgent] Google Gemini API initialized successfully.")
        except Exception as e:
            print(f"[ClubAgent Notice] Gemini API could not be initialized ({e}). Using local rule engine.")
            self.gemini_client = None

    def get_mode(self) -> str:
        """Returns the current operating mode of the agent."""
        if self.gemini_client:
            return "Gemini AI Connected"
        return "Local Knowledge Engine"

    def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Returns all clubs data."""
        return self.clubs

    def get_club_by_id(self, club_id: str) -> Optional[Dict[str, Any]]:
        """Returns a single club by its id."""
        return self.clubs_by_id.get(club_id)

    # -------------------------------------------------------------
    # Local Processing Engine
    # -------------------------------------------------------------
    def answer(self, query: str) -> Dict[str, Any]:
        """
        Main query handling method.
        Dispatches to Gemini if active, or uses local intelligent matcher.
        """
        clean_query = query.strip()
        if not clean_query:
            return {
                "reply": "Please ask a question about our college student clubs! For example: *'How can I join Coding Club?'* or *'What does Robotics Club do?'*",
                "club_id": None,
                "suggestions": ["What clubs are available?", "How to join Coding Club?", "When does AI/ML Club meet?"]
            }

        # If Gemini is configured, attempt Gemini with local fallback
        if self.gemini_client:
            gemini_result = self._query_gemini(clean_query)
            if gemini_result:
                return gemini_result

        # Run local rule & intent matching engine
        return self._local_match(clean_query)

    def _query_gemini(self, query: str) -> Optional[Dict[str, Any]]:
        """Queries Google Gemini model with the JSON knowledge base injected."""
        try:
            context_prompt = (
                f"KNOWLEDGE BASE (COLLEGE CLUBS DATA):\n"
                f"{json.dumps(self.clubs, indent=2)}\n\n"
                f"STUDENT QUESTION: {query}\n\n"
                f"Provide a helpful, well-formatted response. Remember: if the answer is not in the knowledge base, "
                f"clearly state that the information is not available and guide them to the Student Affairs Office."
            )
            response = self.gemini_client.generate_content(context_prompt)
            reply_text = response.text.strip()
            
            # Detect which club was mentioned for frontend highlighting
            detected_club_id = self._detect_club_id(query)
            suggestions = self._generate_suggestions(detected_club_id)

            return {
                "reply": reply_text,
                "club_id": detected_club_id,
                "suggestions": suggestions,
                "source": "gemini"
            }
        except Exception as e:
            print(f"[ClubAgent Error] Gemini request failed: {e}. Falling back to local engine.")
            return None

    def _local_match(self, query: str) -> Dict[str, Any]:
        """
        Intelligent local matcher for offline use.
        Identifies club entity and intent (activities, membership, events, registration, schedule, contact).
        Falls back to 'information not available' when outside knowledge base.
        """
        text = query.lower()

        # 1. Greetings & Meta Queries
        if self._is_greeting(text):
            return {
                "reply": (
                    "👋 **Hello and welcome to the College Club Information Center!**\n\n"
                    "I am your campus AI guide. I can help you explore our student clubs, their weekly activities, "
                    "membership details, upcoming events, and registration procedures.\n\n"
                    "**Available Clubs:**\n"
                    "• 💻 **Coding Club** (ByteCrafters)\n"
                    "• 🤖 **AI/ML Club** (NeuroNet)\n"
                    "• 🦾 **Robotics Club** (MechaTech)\n"
                    "• 🎭 **Cultural Club** (KalaKriti)\n"
                    "• ⚽ **Sports Club** (TitanAthletics)\n\n"
                    "What would you like to know about today?"
                ),
                "club_id": None,
                "suggestions": [
                    "Show all available clubs",
                    "How to join Coding Club?",
                    "What events does AI/ML Club host?",
                    "Which clubs are free to join?"
                ]
            }

        # 2. General Help or "What can you do?"
        if any(p in text for p in ["who are you", "what can you do", "help me", "what is this", "how to use"]):
            return {
                "reply": (
                    "🎓 **Here is what I can help you with:**\n\n"
                    "1. **Club Overview**: Ask about any of our 5 clubs (Coding, AI/ML, Robotics, Cultural, Sports).\n"
                    "2. **Activities & Workshops**: Find out what each club does on a regular basis.\n"
                    "3. **Membership & Fees**: Check eligibility, prerequisites, and registration costs.\n"
                    "4. **Events & Hackathons**: Discover upcoming competitions, fests, and bootcamps.\n"
                    "5. **Meeting Schedules & Venues**: Learn when and where clubs hold their weekly meetups.\n"
                    "6. **Registration Info**: Get registration links, deadlines, and orientation dates.\n\n"
                    "*Note: If you ask about clubs or topics outside our database, I will let you know and direct you to the Student Affairs Office.*"
                ),
                "club_id": None,
                "suggestions": [
                    "List all clubs",
                    "How to register for Robotics Club?",
                    "When does Cultural Club practice?",
                    "Upcoming hackathons & events"
                ]
            }

        # 3. "List all clubs" / "Show me all clubs"
        if any(p in text for p in ["all clubs", "list clubs", "what clubs", "which clubs", "available clubs", "show clubs", "explore clubs"]):
            return self._reply_all_clubs()

        # 4. Global queries: "Which clubs are free?"
        if ("free" in text or "cost" in text or "fee" in text) and not self._detect_club_id(text):
            return self._reply_all_fees()

        # 5. Global queries: "What events are happening?" / "All events"
        if ("events" in text or "hackathon" in text or "competitions" in text or "fests" in text) and not self._detect_club_id(text):
            return self._reply_all_events()

        # 6. Global queries: "How to register?" (across all clubs)
        if any(p in text for p in ["how to register", "how to join", "registration process", "apply"]) and not self._detect_club_id(text):
            return self._reply_all_registration()

        # 7. Identify specific club
        club = self._find_matching_club(text)

        if club:
            return self._handle_club_query(club, text)

        # 8. Unlisted clubs or general out-of-scope campus questions
        return self._reply_not_available(query)

    def _is_greeting(self, text: str) -> bool:
        """Checks if user input is a greeting."""
        cleaned = re.sub(r"[^a-zA-Z\s]", "", text).strip()
        greetings = {"hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening", "namaste"}
        return cleaned in greetings

    def _detect_club_id(self, text: str) -> Optional[str]:
        """Detects if a club ID is mentioned in query."""
        club = self._find_matching_club(text.lower())
        return club["id"] if club else None

    def _find_matching_club(self, text: str) -> Optional[Dict[str, Any]]:
        """Finds the most relevant club based on keywords, name, and aliases."""
        # Direct name checks
        if any(k in text for k in ["coding club", "coding", "programmer", "programming", "code", "leetcode", "dsa", "bytecrafters"]):
            return self.clubs_by_id.get("coding-club")
        if any(k in text for k in ["ai/ml", "ai ml", "ai club", "ml club", "artificial intelligence", "machine learning", "deep learning", "neuronet", "kaggle"]):
            return self.clubs_by_id.get("aiml-club")
        if any(k in text for k in ["robotics club", "robotics", "robot", "arduino", "raspberry pi", "mechatech", "makerspace", "bot fight", "robowars"]):
            return self.clubs_by_id.get("robotics-club")
        if any(k in text for k in ["cultural club", "cultural", "dance", "drama", "theatre", "theater", "acting", "singing", "music", "kalakriti", "open mic"]):
            return self.clubs_by_id.get("cultural-club")
        if any(k in text for k in ["sports club", "sports", "football", "soccer", "cricket", "basketball", "volleyball", "badminton", "athletics", "gym", "titanathletics"]):
            return self.clubs_by_id.get("sports-club")

        # Fallback check against club keywords
        for club in self.clubs:
            for kw in club.get("keywords", []):
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    return club

        return None

    def _handle_club_query(self, club: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Handles queries targeting a specific club by discerning the intent."""
        cid = club["id"]
        cname = club["name"]
        icon = club["icon"]

        # Intent: Activities & Projects
        if any(p in text for p in ["activity", "activities", "what do they do", "what does", "workshops", "sessions", "projects", "learn"]):
            activities_list = "\n".join([f"• {act}" for act in club["activities"]])
            reply = (
                f"{icon} **Activities & Workshops - {cname}**\n\n"
                f"Here are the key activities and regular initiatives conducted by the {cname}:\n\n"
                f"{activities_list}\n\n"
                f"📅 **Regular Meetings**: {club['meeting_schedule']['day']} from {club['meeting_schedule']['time']} at {club['meeting_schedule']['venue']}."
            )
            return {
                "reply": reply,
                "club_id": cid,
                "suggestions": [
                    f"How to register for {cname}?",
                    f"Upcoming events in {cname}",
                    f"Membership fee for {cname}"
                ]
            }

        # Intent: Membership, Fees, Eligibility, Prerequisites
        if any(p in text for p in ["fee", "cost", "price", "membership", "eligible", "eligibility", "prerequisite", "who can join", "freshers", "beginner"]):
            reply = (
                f"{icon} **Membership & Eligibility - {cname}**\n\n"
                f"• **Registration Fee**: **{club['membership']['fee']}**\n"
                f"• **Eligibility**: {club['membership']['eligibility']}\n"
                f"• **Prerequisites**: {club['membership']['prerequisites']}\n\n"
                f"📝 **How to Apply**: {club['registration']['process']}"
            )
            return {
                "reply": reply,
                "club_id": cid,
                "suggestions": [
                    f"When does {cname} meet?",
                    f"What are the activities of {cname}?",
                    f"Who is the president of {cname}?"
                ]
            }

        # Intent: Events & Hackathons & Competitions
        if any(p in text for p in ["event", "events", "hackathon", "competition", "tournament", "fest", "bootcamp", "upcoming", "date"]):
            events_text = ""
            for evt in club["events"]:
                events_text += f"• **{evt['title']}**\n  - 🗓️ *Date*: {evt['date']}\n  - 📍 *Venue*: {evt['venue']}\n  - ℹ️ *Details*: {evt['description']}\n\n"
            reply = (
                f"{icon} **Upcoming Events - {cname}**\n\n"
                f"{events_text}"
                f"📢 Want to participate? Visit their registration desk or check the student portal."
            )
            return {
                "reply": reply,
                "club_id": cid,
                "suggestions": [
                    f"How to register for {cname}?",
                    f"When are {cname} meetings?",
                    f"Who to contact in {cname}?"
                ]
            }

        # Intent: Registration & How to Join & Deadlines
        if any(p in text for p in ["join", "register", "registration", "sign up", "signup", "apply", "admission", "deadline", "form", "link", "orientation"]):
            reply = (
                f"{icon} **Registration & Joining Guide - {cname}**\n\n"
                f"• **Process**: {club['registration']['process']}\n"
                f"• **Registration Link**: [{club['registration']['link']}]({club['registration']['link']})\n"
                f"• **Deadline**: {club['registration']['deadline']}\n"
                f"• **Orientation**: {club['registration']['orientation']}\n\n"
                f"💡 **Membership Fee**: {club['membership']['fee']}"
            )
            return {
                "reply": reply,
                "club_id": cid,
                "suggestions": [
                    f"What activities does {cname} have?",
                    f"When does {cname} meet?",
                    f"Upcoming events in {cname}"
                ]
            }

        # Intent: Meeting Schedule & Timings & Venue
        if any(p in text for p in ["when", "time", "timing", "schedule", "where", "venue", "meet", "meeting", "day", "place", "location"]):
            reply = (
                f"{icon} **Meeting Schedule & Venue - {cname}**\n\n"
                f"• **Meeting Days**: {club['meeting_schedule']['day']}\n"
                f"• **Time**: {club['meeting_schedule']['time']}\n"
                f"• **Location/Venue**: {club['meeting_schedule']['venue']}\n\n"
                f"📍 Need directions? The club room is located at **{club['lead']['room']}**."
            )
            return {
                "reply": reply,
                "club_id": cid,
                "suggestions": [
                    f"What does {cname} do in meetings?",
                    f"How to register for {cname}?",
                    f"Contact info for {cname}"
                ]
            }

        # Intent: Contact / President / Faculty Advisor
        if any(p in text for p in ["contact", "lead", "president", "advisor", "faculty", "email", "in charge", "who runs", "coordinator"]):
            lead = club["lead"]
            reply = (
                f"{icon} **Leadership & Contact - {cname}**\n\n"
                f"• **Student President**: {lead['president']}\n"
                f"• **Faculty Advisor**: {lead['faculty_advisor']}\n"
                f"• **Email**: [{lead['email']}](mailto:{lead['email']})\n"
                f"• **Office / Room**: {lead['room']}\n\n"
                f"Feel free to drop by during office hours or send an email for any queries!"
            )
            return {
                "reply": reply,
                "club_id": cid,
                "suggestions": [
                    f"How to join {cname}?",
                    f"When does {cname} meet?",
                    f"What events does {cname} have?"
                ]
            }

        # Default Club Overview
        activities_summary = "\n".join([f"  • {act}" for act in club["activities"][:2]])
        reply = (
            f"{icon} **{club['name']}** (*{club['short_name']}*)\n"
            f"*{club['tagline']}*\n\n"
            f"{club['description']}\n\n"
            f"**Key Information:**\n"
            f"• 📂 **Category**: {club['category']}\n"
            f"• 💰 **Membership**: {club['membership']['fee']}\n"
            f"• ⏰ **Meets**: {club['meeting_schedule']['day']} ({club['meeting_schedule']['time']})\n"
            f"• 📍 **Venue**: {club['meeting_schedule']['venue']}\n"
            f"• 👤 **President**: {club['lead']['president']}\n"
            f"• ✉️ **Contact**: {club['lead']['email']}\n\n"
            f"**Sample Activities:**\n"
            f"{activities_summary}"
        )
        return {
            "reply": reply,
            "club_id": cid,
            "suggestions": [
                f"How to join {cname}?",
                f"What are all activities of {cname}?",
                f"Upcoming events in {cname}"
            ]
        }

    def _reply_all_clubs(self) -> Dict[str, Any]:
        """Provides an attractive list of all available clubs."""
        lines = []
        for c in self.clubs:
            lines.append(
                f"• {c['icon']} **{c['name']}** ({c['category']})\n"
                f"  *{c['tagline']}*\n"
                f"  Meets: {c['meeting_schedule']['day']} | Fee: {c['membership']['fee']}"
            )
        clubs_formatted = "\n\n".join(lines)
        reply = (
            f"🏛️ **Official College Student Clubs Directory**\n\n"
            f"We have 5 active, officially recognized student clubs:\n\n"
            f"{clubs_formatted}\n\n"
            f"👉 *Click on any club card in the sidebar or ask me specific questions like 'How to join Coding Club?' or 'What does Robotics Club do?'*"
        )
        return {
            "reply": reply,
            "club_id": None,
            "suggestions": [
                "Tell me about Coding Club",
                "What does AI/ML Club do?",
                "Which clubs are free?",
                "Upcoming events"
            ]
        }

    def _reply_all_fees(self) -> Dict[str, Any]:
        """Answers queries regarding fees across all clubs."""
        lines = []
        for c in self.clubs:
            lines.append(f"• {c['icon']} **{c['name']}**: {c['membership']['fee']}")
        fees_formatted = "\n".join(lines)
        reply = (
            f"💰 **Club Membership Fees Overview**\n\n"
            f"{fees_formatted}\n\n"
            f"💡 **Note**: Most of our campus clubs are completely free to join! Robotics Club charges a small \$10 semester fee to cover physical hardware consumables (soldering supplies, 3D printing filament, sensor kits)."
        )
        return {
            "reply": reply,
            "club_id": None,
            "suggestions": [
                "How to register for Robotics Club?",
                "How to join Coding Club?",
                "Show all available clubs"
            ]
        }

    def _reply_all_events(self) -> Dict[str, Any]:
        """Answers queries regarding upcoming events across clubs."""
        event_entries = []
        for c in self.clubs:
            for evt in c.get("events", []):
                event_entries.append(
                    f"• {c['icon']} **{evt['title']}** ({c['name']})\n"
                    f"  🗓️ *{evt['date']}* | 📍 *{evt['venue']}*\n"
                    f"  {evt['description']}"
                )
        events_formatted = "\n\n".join(event_entries)
        reply = (
            f"🎉 **Upcoming College Club Events & Competitions**\n\n"
            f"{events_formatted}\n\n"
            f"Mark your calendar! Reach out to the respective clubs to get registered."
        )
        return {
            
            "reply": reply,
            "club_id": None,
            "suggestions": [
                "How to participate in CodeStorm 2026?",
                "Tell me about RoboWars",
                "When is Spring Fest?"
            ]
        }

    def _reply_all_registration(self) -> Dict[str, Any]:
        """Answers general registration process across all clubs."""
        lines = []
        for c in self.clubs:
            lines.append(f"• {c['icon']} **{c['name']}**: [{c['registration']['link']}]({c['registration']['link']}) (Deadline: {c['registration']['deadline']})")
        reg_formatted = "\n".join(lines)
        reply = (
            f"📝 **Club Registration Portals & Deadlines**\n\n"
            f"You can apply for any student club through the respective portals below:\n\n"
            f"{reg_formatted}\n\n"
            f"✨ You can also sign up in person during the weekly club meetings or at the Student Orientation desk."
        )
        return {
            "reply": reply,
            "club_id": None,
            "suggestions": [
                "Coding Club registration deadline",
                "Robotics Club membership fee",
                "Show all clubs"
            ]
        }

    def _reply_not_available(self, query: str) -> Dict[str, Any]:
        """
        Explicitly triggers when query is outside the available club directory.
        Fulfills requirement: 'If a student asks something outside the available information,
        clearly say that the information is not available.'
        """
        reply = (
            f"⚠️ **Information Not Available**\n\n"
            f"I'm sorry, but that information is not available in my club directory. "
            f"I could not find verified records matching: *\"{query}\"*.\n\n"
            f"Currently, I only provide official details for our **5 registered student clubs**:\n"
            f"• 💻 **Coding Club** (Software, competitive programming, hackathons)\n"
            f"• 🤖 **AI/ML Club** (Artificial intelligence, data science, research)\n"
            f"• 🦾 **Robotics Club** (Hardware, IoT, combat robotics)\n"
            f"• 🎭 **Cultural Club** (Music, dance, theatre, arts & fest)\n"
            f"• ⚽ **Sports Club** (Athletics, intramural tournaments, fitness)\n\n"
            f"📞 **Need help with unlisted clubs, exam schedules, or campus admin?**\n"
            f"Please contact the **Student Affairs Office**:\n"
            f"• **Office**: Student Center, Room 101\n"
            f"• **Email**: [studentaffairs@campus.edu](mailto:studentaffairs@campus.edu)\n"
            f"• **Hours**: Monday – Friday, 9:00 AM – 5:00 PM"
        )
        return {
            "reply": reply,
            "club_id": None,
            "suggestions": [
                "What clubs are available?",
                "Coding Club activities",
                "Robotics Club fee",
                "Sports Club schedule"
            ]
        }

    def _generate_suggestions(self, club_id: Optional[str]) -> List[str]:
        """Generates contextual suggestion pills."""
        if club_id and club_id in self.clubs_by_id:
            cname = self.clubs_by_id[club_id]["name"]
            return [
                f"How to join {cname}?",
                f"What does {cname} do?",
                f"When does {cname} meet?"
            ]
        return [
            "What clubs are available?",
            "How to join Coding Club?",
            "Which clubs are free?",
            "Upcoming hackathons & events"
        ]
