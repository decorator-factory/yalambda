# `yalambda`

Yalambda lets you write Yanex.Cloud Functions with less boilerplate

Features:
- everything is type-annotated, so you'll get autocompletion in IDEs
- base64 de/encoding and other details are handled for you


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

We use the `dataclass-factory` package to parse the JSON request


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
    return YaResponse(200, "Answer:".format(answer))
```