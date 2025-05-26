from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "password_reset_token" VARCHAR(128) UNIQUE;
        ALTER TABLE "user" ADD "password_reset_token_expires_at" TIMESTAMPTZ;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_user_passwor_3ebb43" ON "user" ("password_reset_token");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_user_passwor_3ebb43";
        ALTER TABLE "user" DROP COLUMN "password_reset_token";
        ALTER TABLE "user" DROP COLUMN "password_reset_token_expires_at";"""
