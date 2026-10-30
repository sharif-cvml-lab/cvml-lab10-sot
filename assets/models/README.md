# assets/models/

Two algorithms of the application need a model file. They appear as *unavailable* (with the reason) until the file exists;
everything else keeps working. The other ready-made trackers (CSRT, KCF, MOSSE) need no model.

## MixFormerV2 (the most accurate option)

Put an ONNX export of MixFormerV2 here as

```
assets/models/mixformer_v2.onnx
```

Download link: https://my.sharif.edu/s/LcJXJtSKDa93HgB

## VitTrack

```
assets/models/object_tracking_vittrack_2023sep.onnx
```

The VitTrack model of the OpenCV Zoo (about 1 MB), OpenCV 4.9 or newer. `python tools/download_models.py` tries to download it.
