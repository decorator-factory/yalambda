# `yalambda`

Yalambda lets you write Yanex.Cloud Functions with less boilerplate

Features:
- everything is type-annotated, so you'll get autocompletion in IDEs
- base64 de/encoding and other details are handled for you


# Echo server example

```py
from yalambda import function, YaRequest, YaResponse


@function
async def handler(req: YaRequest) -> YaResponse:
    return YaResponse(200, req.body)
```