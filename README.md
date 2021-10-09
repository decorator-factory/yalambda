# `yalambda`

Yalambda lets you write Yanex.Cloud Functions with less boilerplate

Features:
- everything is type-annotated, so you'll get autocompletion in IDEs
- base64 de/encoding and other details are handled for you
- automatically parse JSON using `dataclass-factory`


# Echo server example

```py
from yalambda import function, YaRequest, YaResponse


@function()
async def handler(req: YaRequest) -> YaResponse:
    return YaResponse(200, req.body)
```


# Automatically parse dataclasses
```py
from dataclasses import dataclass
from yalambda import function, YaResponse


@dataclass
class Point:
    x: float
    y: float


@function()
async def handler(point: Point) -> YaResponse:
    dist = (point.x**2 + point.y**2)**0.5
    return YaResponse(200, {"distance_to_origin": dist})
```


# Access both the dataclass and the request

```py
from dataclasses import dataclass
from yalambda import function, YaRequest, YaResponse


@dataclass
class Point:
    x: float
    y: float


@function()
async def handler(point: Point, req: YaRequest) -> YaResponse:
    if req.http_method != "POST":
        return YaResponse(405, "Only POST requests are allowed")

    dist = (point.x**2 + point.y**2)**0.5
    return YaResponse(200, {"distance_to_origin": dist})
```


# Initialize something asynchronously on first call

```py
from yalambda import function, YaRequest, YaResponse


async def init():
    global answer
    answer = 42


@function(init)
async def handler(req: YaRequest) -> YaResponse:
    return YaResponse(200, "Answer: {}".format(answer))
```


# Routing

```py
from dataclasses import dataclass
from yalambda import dispatch, YaRequest, YaResponse


@dataclass
class Point:
    x: float
    y: float


async def get_all_points(req: YaRequest) -> YaResponse:
    points = [{"x": 3.0, "y": 4.0}, {"x": -1.0, "y": 3.27}]
    return YaResponse(200, points)


async def compute_distance(point: Point) -> YaResponse:
    dist = (point.x**2 + point.y**2)**0.5
    return YaResponse(200, {"distance_to_origin": dist})


handler = dispatch({
    "GET": get_all_points,
    "POST": compute_distance,
})
```


# Full example

This function acts as a GitHub webhook and sends a pretty embed on Discord webhook when an issue is opened or closed. See the source code [on GitHub](https://github.com/decorator-factory/yalambda/tree/master/examples/github-to-discord-webhook).

![Screenshot from Discord showing two embeds](https://imgur.com/Kuoy0XE.png)


# Development server

You can install `aiohttp` and run your function locally.
It's not the same as the real thing, but it should be enough for simple functions.

```bash
$ python -m yalambda your_module
======== Running on http://0.0.0.0:55710 ========
(Press CTRL+C to quit)
```


# Condition DSL

We can modify our GitHub->Discord example so that it doesn't error out on the initial ping event:

```py
from yalambda import when

...

async def handle_issue_events(event: IssueEvent) -> YaResponse:
    embed = create_embed(event)
    if embed is not None:
        await client.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    return YaResponse(200, "")


async def handle_ping(req: YaRequest) -> YaResponse:
    return YaResponse(200, "")


handler = when.dispatch(
    when.header_is("x-github-event", "ping", handle_ping),
    when.header_is("x-github-event", "issues", handle_issue_events),
    init=init
)
```
