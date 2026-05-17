from clipped_voronoi import ClippedVoronoi
from scene import CubeClipping
from utils import read_config


def main():
    config = read_config()
    app = ClippedVoronoi(CubeClipping, config['cube'])
    app.run()


if __name__ == '__main__':
    main()