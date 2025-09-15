# File: utils/redirect_analyzer.py
class RedirectAnalyzer:
    def __init__(self, db):
        self.db = db
    
    async def find_double_redirects(self) -> List[Dict]:
        """Find chains of redirects that need fixing."""
        
        # Get all active redirects
        redirects = await self.db["redirects"].find({"status": "active"}).to_list(length=None)
        
        redirect_map = {}
        for redirect in redirects:
            source = f"{redirect['source_namespace']}:{redirect['source_title']}"
            target = f"{redirect['target_namespace']}:{redirect['target_title']}"
            redirect_map[source] = target
        
        double_redirects = []
        
        for source, intermediate in redirect_map.items():
            if intermediate in redirect_map:
                final_target = redirect_map[intermediate]
                
                # Check for infinite loops
                if final_target == source:
                    continue
                    
                double_redirects.append({
                    "source": source,
                    "intermediate": intermediate, 
                    "final_target": final_target,
                    "chain_length": 2  # Could extend to find longer chains
                })
        
        return double_redirects
    
    async def find_problematic_redirects(self, redirect_type: str) -> List[Dict]:
        """Find specific types of problematic redirects."""
        
        query = {"status": "active"}
        
        if redirect_type == "main_to_user":
            query.update({
                "source_namespace": "",
                "target_namespace": "User"
            })
        elif redirect_type == "broken":
            # Find redirects where target doesn't exist
            pass  # Implementation depends on your data structure
            
        return await self.db["redirects"].find(query).to_list(length=None)
