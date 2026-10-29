"""
Middleware to populate MongoDB user context on Django requests.
"""
from database.repositories.user_repository import UserRepository

class MongoUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            mongo_user = UserRepository.get_by_username(request.user.username)
            request.mongo_user = mongo_user
            if mongo_user:
                request.user_role = mongo_user.get("role", "reviewer")
            else:
                request.user_role = "reviewer"
        else:
            request.mongo_user = None
            request.user_role = "anonymous"

        response = self.get_response(request)
        return response
