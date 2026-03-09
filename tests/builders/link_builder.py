from faker import Faker

fake = Faker()


class LinkBuilder:
    @staticmethod
    def create_payload():
        return {
            "target_url": fake.url(),
        }

    @staticmethod
    def with_custom_code(code: str):
        return {
            "target_url": fake.url(),
            "custom_code": code,
        }

    @staticmethod
    def with_max_clicks(code: str, clicks: int):
        return {
            "target_url": fake.url(),
            "custom_code": code,
            "max_clicks": clicks,
        }

    @staticmethod
    def with_expiration(code: str, expires_at: str):
        return {
            "target_url": fake.url(),
            "custom_code": code,
            "expires_at": expires_at,
        }

    @staticmethod
    def invalid_custom_code():
        return {
            "target_url": "https://example.com",
            "custom_code": "bad code !",
        }