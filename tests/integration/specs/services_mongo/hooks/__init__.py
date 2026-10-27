async def echo(request):
    return {
        "params": request.params,
        "query": request.query,
        "body": request.body,
        "principal": request.principal,
        "inputs": request.inputs,
    }


def refuse(request):
    raise ValueError(f"Refused {request.params['id']}")
