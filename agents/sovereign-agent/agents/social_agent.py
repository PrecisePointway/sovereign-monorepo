#!/usr/bin/env python3
"""
Sovereign Agent - Social Media Automation
ND/ADHD Optimized: Queue once, post automatically, no daily decisions
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import os


class Platform(Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class PostStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"


@dataclass
class SocialPost:
    """A social media post with scheduling."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    platform: Platform = Platform.LINKEDIN
    content: str = ""
    
    # Scheduling
    scheduled_time: Optional[str] = None  # ISO format
    status: PostStatus = PostStatus.DRAFT
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    posted_at: Optional[str] = None
    
    # Optional
    image_path: Optional[str] = None
    link: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    
    # Tracking
    post_url: Optional[str] = None  # URL after posting
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['platform'] = self.platform.value
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SocialPost':
        d['platform'] = Platform(d['platform'])
        d['status'] = PostStatus(d['status'])
        return cls(**d)


class SocialAgent:
    """
    Automated Social Media Management
    
    ND/ADHD Features:
    - Batch content creation (one session, many posts)
    - Automatic posting at optimal times
    - No daily decisions required
    - Weekly content review only
    """
    
    # Optimal posting times (configurable)
    OPTIMAL_TIMES = {
        Platform.LINKEDIN: ["09:00", "12:00", "17:00"],
        Platform.TWITTER: ["08:00", "12:00", "17:00", "20:00"],
        Platform.FACEBOOK: ["09:00", "13:00", "16:00"],
    }
    
    def __init__(self, storage_path: str = "/var/lib/sovereign_agent/social.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.posts: Dict[str, SocialPost] = {}
        self.config = self._load_config()
        self.load()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load API credentials from environment."""
        return {
            "linkedin": {
                "access_token": os.environ.get("LINKEDIN_ACCESS_TOKEN"),
                "enabled": bool(os.environ.get("LINKEDIN_ACCESS_TOKEN"))
            },
            "twitter": {
                "api_key": os.environ.get("TWITTER_API_KEY"),
                "api_secret": os.environ.get("TWITTER_API_SECRET"),
                "access_token": os.environ.get("TWITTER_ACCESS_TOKEN"),
                "access_secret": os.environ.get("TWITTER_ACCESS_SECRET"),
                "enabled": bool(os.environ.get("TWITTER_API_KEY"))
            }
        }
    
    # === Content Creation ===
    
    def create_post(self, platform: Platform, content: str, **kwargs) -> SocialPost:
        """Create a new post (draft by default)."""
        post = SocialPost(
            platform=platform,
            content=content,
            **kwargs
        )
        self.posts[post.id] = post
        self.save()
        return post
    
    def batch_create(self, posts_data: List[Dict[str, Any]]) -> List[SocialPost]:
        """
        Batch create multiple posts at once.
        Perfect for ND/ADHD: one content session, done for the week.
        """
        created = []
        for data in posts_data:
            platform = Platform(data.pop('platform'))
            post = self.create_post(platform, **data)
            created.append(post)
        return created
    
    # === Scheduling ===
    
    def schedule_post(self, post_id: str, scheduled_time: str) -> Optional[SocialPost]:
        """Schedule a post for a specific time."""
        post = self.posts.get(post_id)
        if not post:
            return None
        
        post.scheduled_time = scheduled_time
        post.status = PostStatus.SCHEDULED
        self.save()
        return post
    
    def auto_schedule(self, post_id: str, days_ahead: int = 1) -> Optional[SocialPost]:
        """
        Automatically schedule at next optimal time.
        No decision required - system picks the best slot.
        """
        post = self.posts.get(post_id)
        if not post:
            return None
        
        optimal_times = self.OPTIMAL_TIMES.get(post.platform, ["12:00"])
        
        # Find next available slot
        target_date = datetime.now().date() + timedelta(days=days_ahead)
        
        for time_str in optimal_times:
            scheduled = f"{target_date.isoformat()}T{time_str}:00"
            
            # Check if slot is free
            if not self._slot_taken(post.platform, scheduled):
                post.scheduled_time = scheduled
                post.status = PostStatus.SCHEDULED
                self.save()
                return post
        
        # If all slots taken, use first slot next day
        target_date += timedelta(days=1)
        post.scheduled_time = f"{target_date.isoformat()}T{optimal_times[0]}:00"
        post.status = PostStatus.SCHEDULED
        self.save()
        return post
    
    def auto_schedule_week(self, platform: Platform) -> int:
        """
        Auto-schedule all drafts for the week.
        One command, week of content scheduled.
        """
        drafts = [p for p in self.posts.values() 
                  if p.platform == platform and p.status == PostStatus.DRAFT]
        
        scheduled_count = 0
        for i, post in enumerate(drafts):
            days_ahead = i // len(self.OPTIMAL_TIMES.get(platform, ["12:00"])) + 1
            if self.auto_schedule(post.id, days_ahead):
                scheduled_count += 1
        
        return scheduled_count
    
    def _slot_taken(self, platform: Platform, scheduled_time: str) -> bool:
        """Check if a time slot is already taken."""
        for post in self.posts.values():
            if (post.platform == platform 
                and post.scheduled_time == scheduled_time
                and post.status == PostStatus.SCHEDULED):
                return True
        return False
    
    # === Posting ===
    
    def get_due_posts(self) -> List[SocialPost]:
        """Get posts that are due for posting."""
        now = datetime.now().isoformat()
        return [p for p in self.posts.values()
                if p.status == PostStatus.SCHEDULED
                and p.scheduled_time
                and p.scheduled_time <= now]
    
    def post_now(self, post_id: str) -> Dict[str, Any]:
        """
        Post immediately.
        Returns result with success/failure info.
        """
        post = self.posts.get(post_id)
        if not post:
            return {"success": False, "error": "Post not found"}
        
        try:
            result = self._execute_post(post)
            
            if result["success"]:
                post.status = PostStatus.POSTED
                post.posted_at = datetime.now().isoformat()
                post.post_url = result.get("url")
            else:
                post.status = PostStatus.FAILED
                post.error = result.get("error")
            
            self.save()
            return result
            
        except Exception as e:
            post.status = PostStatus.FAILED
            post.error = str(e)
            self.save()
            return {"success": False, "error": str(e)}
    
    def _execute_post(self, post: SocialPost) -> Dict[str, Any]:
        """Execute the actual posting to platform API."""
        
        if post.platform == Platform.LINKEDIN:
            return self._post_linkedin(post)
        elif post.platform == Platform.TWITTER:
            return self._post_twitter(post)
        else:
            return {"success": False, "error": f"Platform {post.platform} not implemented"}
    
    def _post_linkedin(self, post: SocialPost) -> Dict[str, Any]:
        """Post to LinkedIn API."""
        if not self.config["linkedin"]["enabled"]:
            return {"success": False, "error": "LinkedIn not configured"}
        
        # LinkedIn API implementation
        # Using LinkedIn Marketing API
        try:
            import requests
            
            access_token = self.config["linkedin"]["access_token"]
            
            # Get user URN first
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Create post
            post_data = {
                "author": "urn:li:person:REPLACE_WITH_URN",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post.content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Note: In production, make actual API call
            # response = requests.post(
            #     "https://api.linkedin.com/v2/ugcPosts",
            #     headers=headers,
            #     json=post_data
            # )
            
            # Simulated success for now
            return {
                "success": True,
                "url": f"https://linkedin.com/posts/{post.id}",
                "message": "Posted to LinkedIn (simulated)"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _post_twitter(self, post: SocialPost) -> Dict[str, Any]:
        """Post to Twitter/X API."""
        if not self.config["twitter"]["enabled"]:
            return {"success": False, "error": "Twitter not configured"}
        
        try:
            # Twitter API v2 implementation
            # Note: In production, use tweepy or twitter-api-v2
            
            # Simulated success for now
            return {
                "success": True,
                "url": f"https://twitter.com/status/{post.id}",
                "message": "Posted to Twitter (simulated)"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_scheduled(self) -> List[Dict[str, Any]]:
        """
        Process all due scheduled posts.
        Called by cron/scheduler.
        """
        results = []
        for post in self.get_due_posts():
            result = self.post_now(post.id)
            result["post_id"] = post.id
            results.append(result)
        return results
    
    # === Content Templates ===
    
    def generate_from_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """Generate post content from template."""
        templates = {
            "release": """🚀 {product} {version} released.

{features}

Documentation: {link}

#OpenSource #AIGovernance""",
            
            "insight": """{insight}

{elaboration}

#AIGovernance #DataSovereignty""",
            
            "thread_start": """🧵 {title}

{hook}

Thread below 👇""",
        }
        
        template = templates.get(template_name, "{content}")
        return template.format(**variables)
    
    # === Queue Management ===
    
    def get_queue(self, platform: Optional[Platform] = None) -> List[SocialPost]:
        """Get all scheduled posts."""
        posts = [p for p in self.posts.values() if p.status == PostStatus.SCHEDULED]
        if platform:
            posts = [p for p in posts if p.platform == platform]
        posts.sort(key=lambda p: p.scheduled_time or "")
        return posts
    
    def get_drafts(self, platform: Optional[Platform] = None) -> List[SocialPost]:
        """Get all draft posts."""
        posts = [p for p in self.posts.values() if p.status == PostStatus.DRAFT]
        if platform:
            posts = [p for p in posts if p.platform == platform]
        return posts
    
    # === Analytics (Minimal) ===
    
    def weekly_summary(self) -> Dict[str, Any]:
        """
        Weekly summary only - no daily noise.
        ND/ADHD optimized: one check per week.
        """
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        posted = [p for p in self.posts.values()
                  if p.status == PostStatus.POSTED
                  and p.posted_at and p.posted_at >= week_ago]
        
        scheduled = [p for p in self.posts.values()
                     if p.status == PostStatus.SCHEDULED]
        
        drafts = [p for p in self.posts.values()
                  if p.status == PostStatus.DRAFT]
        
        return {
            "posted_this_week": len(posted),
            "scheduled_upcoming": len(scheduled),
            "drafts_pending": len(drafts),
            "platforms": {
                "linkedin": len([p for p in posted if p.platform == Platform.LINKEDIN]),
                "twitter": len([p for p in posted if p.platform == Platform.TWITTER]),
            },
            "next_post": min([p.scheduled_time for p in scheduled], default=None)
        }
    
    # === Persistence ===
    
    def save(self):
        """Save posts to disk."""
        data = {
            "posts": {k: v.to_dict() for k, v in self.posts.items()},
            "saved_at": datetime.now().isoformat()
        }
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def load(self):
        """Load posts from disk."""
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            self.posts = {k: SocialPost.from_dict(v) for k, v in data.get("posts", {}).items()}


# === CLI Interface ===

if __name__ == "__main__":
    agent = SocialAgent("/tmp/test_social.json")
    
    print("=== Sovereign Agent - Social Media ===")
    print("ND/ADHD Optimized: Queue once, post automatically\n")
    
    # Create sample posts
    agent.create_post(
        Platform.LINKEDIN,
        "S.A.F.E.-OS v1.0.0 is now available.\n\nKey features:\n• Language Safety Gate\n• Data Sovereignty endpoints\n• Explanation Layer\n\n#AIGovernance #OpenSource"
    )
    
    agent.create_post(
        Platform.TWITTER,
        "The distinction matters:\n\nMirror systems optimize for engagement.\nTool systems optimize for task completion.\n\nOne extracts. One serves."
    )
    
    # Auto-schedule all drafts
    print("Auto-scheduling drafts...")
    for platform in [Platform.LINKEDIN, Platform.TWITTER]:
        count = agent.auto_schedule_week(platform)
        print(f"  {platform.value}: {count} posts scheduled")
    
    # Show queue
    print("\nScheduled Queue:")
    for post in agent.get_queue():
        print(f"  [{post.platform.value}] {post.scheduled_time}: {post.content[:50]}...")
    
    # Weekly summary
    print("\nWeekly Summary:")
    summary = agent.weekly_summary()
    print(f"  Drafts pending: {summary['drafts_pending']}")
    print(f"  Scheduled: {summary['scheduled_upcoming']}")
    print(f"  Next post: {summary['next_post']}")
    
    print("\n✓ Social Agent Test Complete")
