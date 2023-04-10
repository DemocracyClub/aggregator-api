import os


def init_sentry():
    if sentry_dsn := os.environ.get("SENTRY_DSN"):
        import sentry_sdk
        from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                AwsLambdaIntegration(),
            ],
        )
