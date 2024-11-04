from typing import List, Dict, Optional
from enum import Enum
import hashlib

# Enum for Role Definitions
class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SUPERVISOR = "supervisor"

# User Class to Represent the System's Users
class User:
    def __init__(self, username: str, roles: List[Role]):
        self.username = username
        self.roles = roles

    def has_role(self, role: Role) -> bool:
        return role in self.roles

    def __str__(self):
        return f"User(username={self.username}, roles={self.roles})"

# Permissions Definitions
class Permission(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"

# Resource Class Representing a Protected System Resource
class Resource:
    def __init__(self, resource_id: str, owner: User):
        self.resource_id = resource_id
        self.owner = owner
        self.permissions: Dict[User, List[Permission]] = {}

    def add_permission(self, user: User, permission: Permission):
        if user not in self.permissions:
            self.permissions[user] = []
        if permission not in self.permissions[user]:
            self.permissions[user].append(permission)

    def check_permission(self, user: User, permission: Permission) -> bool:
        return permission in self.permissions.get(user, [])

    def __str__(self):
        return f"Resource(resource_id={self.resource_id}, owner={self.owner})"

# Role-Based Access Control (RBAC) System
class RBACSystem:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.resources: Dict[str, Resource] = {}

    def create_user(self, username: str, roles: List[Role]) -> User:
        if username in self.users:
            raise ValueError(f"User {username} already exists.")
        user = User(username, roles)
        self.users[username] = user
        return user

    def create_resource(self, resource_id: str, owner_username: str) -> Resource:
        if owner_username not in self.users:
            raise ValueError(f"User {owner_username} does not exist.")
        owner = self.users[owner_username]
        resource = Resource(resource_id, owner)
        self.resources[resource_id] = resource
        return resource

    def assign_permission(self, resource_id: str, username: str, permission: Permission):
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist.")
        if username not in self.users:
            raise ValueError(f"User {username} does not exist.")
        
        resource = self.resources[resource_id]
        user = self.users[username]
        resource.add_permission(user, permission)

    def check_access(self, username: str, resource_id: str, permission: Permission) -> bool:
        if username not in self.users:
            raise ValueError(f"User {username} does not exist.")
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist.")
        
        user = self.users[username]
        resource = self.resources[resource_id]
        
        # Check if user is resource owner
        if resource.owner == user:
            return True
        
        # Check if user has specific permission
        if resource.check_permission(user, permission):
            return True
        
        # Check roles if user has admin or supervisor privileges
        if user.has_role(Role.ADMIN) or user.has_role(Role.SUPERVISOR):
            return True
        
        return False

# Authorization Manager to Handle Higher-Level Operations
class AuthorizationManager:
    def __init__(self, rbac_system: RBACSystem):
        self.rbac_system = rbac_system

    def request_access(self, username: str, resource_id: str, permission: Permission) -> bool:
        try:
            has_access = self.rbac_system.check_access(username, resource_id, permission)
            if has_access:
                print(f"Access granted to {username} for {permission.value} on {resource_id}.")
            else:
                print(f"Access denied for {username} for {permission.value} on {resource_id}.")
            return has_access
        except ValueError as e:
            print(f"Error: {str(e)}")
            return False

# Usage
if __name__ == "__main__":
    rbac = RBACSystem()

    # Creating Users
    admin = rbac.create_user("admin", [Role.ADMIN])
    user = rbac.create_user("user", [Role.USER])
    guest = rbac.create_user("guest", [Role.GUEST])
    supervisor = rbac.create_user("supervisor", [Role.SUPERVISOR])

    # Creating a Resource
    resource1 = rbac.create_resource("resource1", "admin")

    # Assigning Permissions
    rbac.assign_permission("resource1", "user", Permission.READ)
    rbac.assign_permission("resource1", "guest", Permission.READ)
    rbac.assign_permission("resource1", "supervisor", Permission.WRITE)

    # Authorization Manager Instance
    auth_manager = AuthorizationManager(rbac)

    # Check Access
    auth_manager.request_access("admin", "resource1", Permission.DELETE) 
    auth_manager.request_access("user", "resource1", Permission.READ)     
    auth_manager.request_access("user", "resource1", Permission.WRITE)    
    auth_manager.request_access("guest", "resource1", Permission.READ)    
    auth_manager.request_access("guest", "resource1", Permission.WRITE)   
    auth_manager.request_access("supervisor", "resource1", Permission.WRITE)  
    auth_manager.request_access("supervisor", "resource1", Permission.EXECUTE) 