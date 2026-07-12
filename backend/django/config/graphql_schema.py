import strawberry
from graphql import GraphQLError
from strawberry.extensions.query_depth_limiter import QueryDepthLimiter

from config.graphql_mutations import Mutation
from config.graphql_queries import Query


class HumanReadyGraphQLSchema(strawberry.Schema):
    def process_errors(self, errors, execution_context=None) -> None:
        unexpected_errors = [
            error
            for error in errors
            if error.original_error is not None
            and not isinstance(error.original_error, GraphQLError)
        ]
        if unexpected_errors:
            super().process_errors(unexpected_errors, execution_context)


schema = HumanReadyGraphQLSchema(
    query=Query,
    mutation=Mutation,
    extensions=[QueryDepthLimiter(max_depth=6)],
)
