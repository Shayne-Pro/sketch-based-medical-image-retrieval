# Sketch-Based Medical Image Retrieval

This repository contains the official implementation of the sketch-based medical image retrieval (SBMIR) system described in the paper **"Sketch-based semantic retrieval of medical images"** by Kazuma Kobayashi et al. in the _Medical Image Analysis_ (2024).

## Overview

The SBMIR system enables users to retrieve medical images based on sketches of abnormalities and template images representing normal anatomy. The key components of the system are:

- Feature extraction module: Decomposes medical images into normal anatomy codes (ACs) and abnormal ACs using a deep learning framework.
- Similarity calculation module: Retrieves reference images based on the similarity between query vectors (constructed from user sketches and template images) and reference vectors (extracted from reference images).

## Repository Structure

- `App/`: Contains the implementation of the SBMIR system. By setting up the same environment, you can experience how the SBMIR system operates in practice.
- `ModelTraining/`: _(Under preparation)_ Will contain the learning algorithm for the feature extraction module of the SBMIR system.

Please note that currently, only the `App/` folder is available for public use. The contents of the `ModelTraining/` folder are still under preparation.

## Data

The glioma dataset used in the paper is available from the MICCAI BraTS Challenge. The lung cancer dataset was collected from a single hospital and remains under their custody.

## Citation

If you use this code or the SBMIR system in your research, please cite the following paper:

```
@article{KOBAYASHI2024103060,
    title = {Sketch-based semantic retrieval of medical images},
    author = {Kazuma Kobayashi and Lin Gu and Ryuichiro Hataya and Takaaki Mizuno and Mototaka Miyake and Hirokazu Watanabe and Masamichi Takahashi and Yasuyuki Takamizawa and Yukihiro Yoshida and Satoshi Nakamura and Nobuji Kouno and Amina Bolatkan and Yusuke Kurose and Tatsuya Harada and Ryuji Hamamoto},
    year = 2024,
    journal = {Medical Image Analysis},
    volume = 92,
    pages = 103060,
    doi = {https://doi.org/10.1016/j.media.2023.103060},
    issn = {1361-8415},
    url = {https://www.sciencedirect.com/science/article/pii/S1361841523003201},
    keywords = {Sketch-based image retrieval, Content-based image retrieval, Feature decomposition, Query by sketch, Query by example},
}
```

## License

This project is licensed under the terms of the CC-BY-NC-4.0 license.
