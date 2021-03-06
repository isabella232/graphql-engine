# -*- coding: utf-8 -*-

from http import HTTPStatus

import graphene

from webserver import RequestHandler, WebServer, MkHandlers, Response

from enum import Enum

def mkJSONResp(graphql_result):
    return Response(HTTPStatus.OK, graphql_result.to_dict(),
                    {'Content-Type': 'application/json'})


class HelloWorldHandler(RequestHandler):
    def get(self, request):
        return Response(HTTPStatus.OK, 'hello world')

    def post(self, request):
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

class Hello(graphene.ObjectType):
    hello = graphene.String(arg=graphene.String(default_value="world"))

    def resolve_hello(self, info, arg):
        return "Hello " + arg

hello_schema = graphene.Schema(query=Hello, subscription=Hello)

class HelloGraphQL(RequestHandler):
    def get(self, request):
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    def post(self, request):
        if not request.json:
            return Response(HTTPStatus.BAD_REQUEST)
        res = hello_schema.execute(request.json['query'])
        return mkJSONResp(res)

class User(graphene.ObjectType):
    id = graphene.Int()
    username = graphene.String()
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def resolve_id(self, info):
        return self.id

    def resolve_username(self, info):
        return self.username

    @staticmethod
    def get_by_id(_id):
        xs = list(filter(lambda u: u.id == _id, all_users))
        if not xs:
            return None
        return xs[0]

all_users = [
    User(1, 'jane'),
    User(2, 'john'),
    User(3, 'joe'),
]

class CreateUser(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        username = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(lambda: User)

    def mutate(self, info, id, username):
        user = User(id, username)
        all_users.append(user)
        return CreateUser(ok=True, user=user)

class UserQuery(graphene.ObjectType):
    user = graphene.Field(User, id=graphene.Int(required=True))
    allUsers = graphene.List(User)

    def resolve_user(self, info, id):
        return User.get_by_id(id)

    def resolve_allUsers(self, info):
        return all_users

class UserMutation(graphene.ObjectType):
    createUser = CreateUser.Field()
user_schema = graphene.Schema(query=UserQuery, mutation=UserMutation)

class UserGraphQL(RequestHandler):
    def get(self, req):
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    def post(self, req):
        if not req.json:
            return Response(HTTPStatus.BAD_REQUEST)
        res = user_schema.execute(req.json['query'])
        return mkJSONResp(res)

class timestamptz(graphene.types.Scalar):
    @staticmethod
    def serialize(t):
        return "2018-12-20"
    @staticmethod
    def parse_literal(s):
        return "2018-12-20"
    @staticmethod
    def parse_value(s):
        return "2018-12-20"

class Country(graphene.ObjectType):
    name = graphene.String()

    def __init__(self, name):
        self.name = name

    def resolve_name(self, info):
        return self.name

class CountryQuery(graphene.ObjectType):
    country = graphene.Field(Country)

    def resolve_country(self, info):
        return Country("India")

country_schema = graphene.Schema(query=CountryQuery)

class CountryGraphQL(RequestHandler):
    def get(self, req):
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    def post(self, req):
        if not req.json:
            return Response(HTTPStatus.BAD_REQUEST)
        res = country_schema.execute(req.json['query'])
        return mkJSONResp(res)


class person(graphene.ObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    created = graphene.Field(timestamptz)

    def resolve_id(self, info):
        return 42
    def resolve_name(self, info):
        return 'Arthur Dent'
    def resolve_created(self, info):
        return '2018-12-20'

class PersonQuery(graphene.ObjectType):
    person_ = graphene.Field(person)

    def resolve_person_(self, info):
        return person()

person_schema = graphene.Schema(query=PersonQuery)

class PersonGraphQL(RequestHandler):
    def get(self, req):
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    def post(self, req):
        if not req.json:
            return Response(HTTPStatus.BAD_REQUEST)
        res = person_schema.execute(req.json['query'])
        return mkJSONResp(res)

class InpObjType(graphene.InputObjectType):

    @classmethod
    def default(cls):
        meta = cls._meta
        fields = meta.fields
        default_fields = {name: field.default_value for name, field in fields.items()}
        container = meta.container
        return container(**default_fields)

class SizeObj(graphene.ObjectType):
    width = graphene.Int()
    height = graphene.Float()
    shape = graphene.String()
    hasTag = graphene.Boolean()
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

GQColorEnum = graphene.Enum.from_enum(Color)

class SizeInput(InpObjType):
    width = graphene.Int(default_value=100)
    height = graphene.Float(default_value=100.1)
    shape = graphene.String(default_value="cube")
    hasTag = graphene.Boolean(default_value=False)

    def asSizeObj(self):
        return SizeObj(width=self.width, height=self.height, shape=self.shape, hasTag=self.hasTag)


class Echo(graphene.ObjectType):
    intFld = graphene.Int()
    listFld = graphene.List(graphene.String)
    objFld = graphene.Field(SizeObj)
    enumFld = graphene.Field(GQColorEnum)

class EchoQuery(graphene.ObjectType):
    echo = graphene.Field(
                Echo,
                int_input=graphene.Int( default_value=1234),
                list_input=graphene.Argument(graphene.List(graphene.String), default_value=["hi","there"]),
                obj_input=graphene.Argument(SizeInput, default_value=SizeInput.default()),
                enum_input=graphene.Argument(GQColorEnum, default_value=GQColorEnum.RED.name),
            )

    def resolve_echo(self, info, int_input, list_input, obj_input, enum_input):
        #print (int_input, list_input, obj_input)
        return Echo(intFld=int_input, listFld=list_input, objFld=obj_input, enumFld=enum_input)

echo_schema = graphene.Schema(query=EchoQuery)

class EchoGraphQL(RequestHandler):
    def get(self, req):
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    def post(self, req):
        if not req.json:
            return Response(HTTPStatus.BAD_REQUEST)
        res = echo_schema.execute(req.json['query'])
        respDict = res.to_dict()
        typesList = respDict.get('data',{}).get('__schema',{}).get('types',None)
        if typesList is not None:
            for t in filter(lambda ty: ty['name'] == 'EchoQuery', typesList):
                for f in filter(lambda fld: fld['name'] == 'echo', t['fields']):
                    for a in filter(lambda arg: arg['name'] == 'enumInput', f['args']):
                        a['defaultValue'] = 'RED'
        return Response(HTTPStatus.OK, respDict,
                    {'Content-Type': 'application/json'})

handlers = MkHandlers({
    '/hello': HelloWorldHandler,
    '/hello-graphql': HelloGraphQL,
    '/user-graphql': UserGraphQL,
    '/country-graphql': CountryGraphQL,
    '/default-value-echo-graphql' : EchoGraphQL,
    '/person-graphql': PersonGraphQL
})


def create_server(host='127.0.0.1', port=5000):
    return WebServer((host, port), handlers)

def stop_server(server):
    server.shutdown()
    server.server_close()

if __name__ == '__main__':
    s = create_server(host='0.0.0.0')
    s.serve_forever()
