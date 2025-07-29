import asyncio
from typing import Dict, Any, Optional
import time

class InMemoryDatabase:
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task = None
        
    async def start_cleanup_task(self):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def stop_cleanup_task(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
    async def _periodic_cleanup(self):
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup task: {e}")
                
    async def cleanup_expired(self, max_age_seconds: int = 3600):
        current_time = time.time()
        expired_keys = []
        
        for key, data in self._data.items():
            if current_time - data.get('created_at', 0) > max_age_seconds:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self._data[key]
            
        if expired_keys:
            print(f"Cleaned up {len(expired_keys)} expired entries")
            
    def set_user_data(self, user_id: int, data: Dict[str, Any]):
        key = str(user_id)
        self._data[key] = {
            **data,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        key = str(user_id)
        if key in self._data:
            data = self._data[key].copy()
            data['updated_at'] = time.time()
            self._data[key] = data
            return data
        return None
        
    def update_user_data(self, user_id: int, updates: Dict[str, Any]):
        key = str(user_id)
        if key in self._data:
            self._data[key].update(updates)
            self._data[key]['updated_at'] = time.time()
        else:
            self.set_user_data(user_id, updates)
            
    def delete_user_data(self, user_id: int):
        key = str(user_id)
        if key in self._data:
            del self._data[key]
            
    def clear_all(self):
        self._data.clear()
        
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        return self._data.copy()

db = InMemoryDatabase()