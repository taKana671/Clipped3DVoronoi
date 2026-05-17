from clipped_voronoi import ClippedVoronoi
from scene import SphereClipping
from utils import read_config


def main():
    config = read_config()
    app = ClippedVoronoi(SphereClipping, config['sphere'])
    app.run()


if __name__ == '__main__':
    main()