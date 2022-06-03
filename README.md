# 3D plots using Blender as a backend

```bash
docker run -t -d \
    --gpus all \
    --net host \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $PWD:/home/docker/workspace \
    -e DISPLAY=$DISPLAY \
    --name belnder-plot-dev \
    blender-py
```
