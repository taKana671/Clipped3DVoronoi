# Clipped3DVoronoi

I used SciPy’s `scipy.spatial.Voronoi` to perform a 3D Voronoi partition, calculated the vertices of the Voronoi regions (polyhedra), and clipped them with a cube. Finally, I created 3D models of the Voronoi regions from the clipped vertices.
Clone the repository, run `clipped_voronoi.py`, and press the [U] key on your keyboard. A force is applied to each model, causing the cube to collapse.
The parameters for the Voronoi partition and the 3D model are managed in `clipping_config.yaml`.
If you want to increase the number of Voronoi partitions (`cut_points`) or the number of times the 3D model’s faces are subdivided into triangles (`max_depth`), setting `multi_processing` to `true`
will speed up the creation of the 3D models.


https://github.com/user-attachments/assets/3e22177f-7adf-4b17-9da3-19c6ed141d06


# Requirements

* Panda3D 1.10.16
* numpy 2.2.6
* scipy 1.16.2
* shapely 2.1.2
* PyYAML 6.0.3
  
# Environment

* Python 3.13
* Windows11

# Usage

### Clone this repository with submodule.
```
git clone --recursive https://github.com/taKana671/Clipped3DVoronoi.git
```

### Execute the following command
```
python clipped_voronoi.py
```

### Key control

<table>
    <tr>
      <th>key</th>
      <th>description</th>
    </tr>
    <tr>
      <th>Esc</th>
      <th align="left">Close the screen.</th>
    </tr>
    <tr>
      <th>d</th>
      <th align="left">Toggles physical object display on and off.</th>
    </tr>
    <tr>
      <th>w</th>
      <th align="left">Toggles wireframe display on and off.</th>
    </tr>
    <tr>
      <th>u</th>
      <th align="left">Apply force to each voronoi region model.</th>
    </tr>
</table>

### Parameters

If you edit `clipping_config.yaml` and then run `clipped_voronoi.py`, the updated values will be reflected in the output.

<table>
    <tr>
      <th>parameter</th>
      <th>data type</th>
      <th>default</th>
      <th>description</th>
    </tr>
    <tr>
      <th>cut_points</th>
      <th>int</th>
      <th>30</th>
      <th align="left">The number of polyhedrons to divide a cube into.</th>
    </tr>
    <tr>
      <th>cube_size</th>
      <th>float</th>
      <th>1</th>
      <th align="left">Length of a cube's edge. <br> Must be greater than 0.</th>
    </tr>
    <tr>
      <th>diff</th>
      <th>float</th>
      <th>0.5</th>
      <th align="left">How far from the vertices of the cube the dummy points should be placed. <br> Must be greater than 0.</th>
    </tr>
    <tr>
      <th>max_depth</th>
      <th>int</th>
      <th>2</th>
      <th align="left">The number of divisions of one triangle. <br> Must be greater than 0.</th>
    </tr>
    <tr>
      <th>scale</th>
      <th>int</th>
      <th>2</th>
      <th align="left">The scale of the polyhedron. <br> Must be greater than 0.</th>
    </tr>
    <tr>
      <th>multi_processing</th>
      <th>bool</th>
      <th>false</th>
      <th align="left">true or false. <br> If true, the 3D models are created using multiprocessing.</th>
    </tr>
</table>

