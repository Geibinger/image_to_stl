#!/usr/bin/env python3
import argparse
from PIL import Image
import numpy as np

def compute_normal(v1, v2, v3):
    """
    Compute the normal vector of the triangle defined by vertices v1, v2, and v3.
    """
    v1 = np.array(v1)
    v2 = np.array(v2)
    v3 = np.array(v3)
    normal = np.cross(v2 - v1, v3 - v1)
    norm = np.linalg.norm(normal)
    if norm == 0:
        return (0.0, 0.0, 0.0)
    return tuple(normal / norm)

def add_triangle(facets, v1, v2, v3):
    """
    Add a triangle (facet) defined by v1, v2, v3 to the facets list.
    """
    normal = compute_normal(v1, v2, v3)
    facets.append((normal, v1, v2, v3))

def generate_binary_mesh(args, img_array):
    """
    Generate a closed mesh in binary mode. In this mode each pixel is considered
    individually. For each pixel that is 'solid' (intensity below threshold),
    a top face, bottom face, and side walls (only if the neighboring pixel is not solid)
    are created.
    """
    facets = []
    rows, cols = img_array.shape
    # In binary mode, treat each pixel as a cell of size:
    x_scale = args.x_size / cols
    y_scale = args.y_size / rows
    threshold = args.threshold

    for j in range(rows):
        for i in range(cols):
            if img_array[j, i] < threshold:  # Consider pixel as solid if "black"
                # Define the XY boundaries of the cell
                x0 = i * x_scale
                x1 = (i + 1) * x_scale
                y0 = j * y_scale
                y1 = (j + 1) * y_scale
                z_top = args.extrude_height
                z_bottom = 0.0

                # Top face (oriented upward)
                top_v0 = (x0, y0, z_top)
                top_v1 = (x1, y0, z_top)
                top_v2 = (x1, y1, z_top)
                top_v3 = (x0, y1, z_top)
                add_triangle(facets, top_v0, top_v1, top_v2)
                add_triangle(facets, top_v0, top_v2, top_v3)

                # Bottom face (oriented downward)
                bot_v0 = (x0, y0, z_bottom)
                bot_v1 = (x1, y0, z_bottom)
                bot_v2 = (x1, y1, z_bottom)
                bot_v3 = (x0, y1, z_bottom)
                add_triangle(facets, bot_v2, bot_v1, bot_v0)
                add_triangle(facets, bot_v3, bot_v2, bot_v0)

                # Walls – check each side to see if a neighbor is not solid
                # Left wall
                if i == 0 or img_array[j, i - 1] >= threshold:
                    v_top1 = (x0, y0, z_top)
                    v_top2 = (x0, y1, z_top)
                    v_bot1 = (x0, y0, z_bottom)
                    v_bot2 = (x0, y1, z_bottom)
                    add_triangle(facets, v_top2, v_top1, v_bot1)
                    add_triangle(facets, v_top2, v_bot1, v_bot2)
                # Right wall
                if i == cols - 1 or img_array[j, i + 1] >= threshold:
                    v_top1 = (x1, y0, z_top)
                    v_top2 = (x1, y1, z_top)
                    v_bot1 = (x1, y0, z_bottom)
                    v_bot2 = (x1, y1, z_bottom)
                    add_triangle(facets, v_top1, v_top2, v_bot1)
                    add_triangle(facets, v_top2, v_bot2, v_bot1)
                # Top wall
                if j == 0 or img_array[j - 1, i] >= threshold:
                    v_top1 = (x0, y0, z_top)
                    v_top2 = (x1, y0, z_top)
                    v_bot1 = (x0, y0, z_bottom)
                    v_bot2 = (x1, y0, z_bottom)
                    add_triangle(facets, v_top2, v_top1, v_bot1)
                    add_triangle(facets, v_top2, v_bot1, v_bot2)
                # Bottom wall
                if j == rows - 1 or img_array[j + 1, i] >= threshold:
                    v_top1 = (x0, y1, z_top)
                    v_top2 = (x1, y1, z_top)
                    v_bot1 = (x0, y1, z_bottom)
                    v_bot2 = (x1, y1, z_bottom)
                    add_triangle(facets, v_top1, v_top2, v_bot1)
                    add_triangle(facets, v_top2, v_bot2, v_bot1)
    return facets

def generate_continuous_mesh(args, img_array):
    """
    Generate a closed mesh in continuous mode. The image is converted to a grid,
    where pixel intensity is mapped linearly to a height between 0 and extrude_height.
    Then a top surface is created along with side walls around the entire boundary
    and a bottom face.
    """
    rows, cols = img_array.shape
    x_scale = args.x_size / (cols - 1)
    y_scale = args.y_size / (rows - 1)
    z_array = (img_array / 255.0) * args.extrude_height

    # Create a grid of top surface vertices.
    top_vertices = np.empty((rows, cols, 3))
    for j in range(rows):
        for i in range(cols):
            x = i * x_scale
            y = j * y_scale
            z = z_array[j, i]
            top_vertices[j, i] = (x, y, z)

    facets = []
    # Top surface triangles
    for j in range(rows - 1):
        for i in range(cols - 1):
            v1 = top_vertices[j, i]
            v2 = top_vertices[j, i + 1]
            v3 = top_vertices[j + 1, i]
            v4 = top_vertices[j + 1, i + 1]
            add_triangle(facets, v1, v2, v3)
            add_triangle(facets, v2, v4, v3)

    # Bottom face covering the entire base
    bottom_top_left     = (0.0, 0.0, 0.0)
    bottom_top_right    = (args.x_size, 0.0, 0.0)
    bottom_bottom_left  = (0.0, args.y_size, 0.0)
    bottom_bottom_right = (args.x_size, args.y_size, 0.0)
    add_triangle(facets, bottom_top_left, bottom_top_right, bottom_bottom_left)
    add_triangle(facets, bottom_top_right, bottom_bottom_right, bottom_bottom_left)

    # Side walls along the boundary of the grid.
    # Top edge (j = 0)
    j = 0
    for i in range(cols - 1):
        v_top1 = top_vertices[j, i]
        v_top2 = top_vertices[j, i + 1]
        v_bot1 = (v_top1[0], v_top1[1], 0.0)
        v_bot2 = (v_top2[0], v_top2[1], 0.0)
        add_triangle(facets, v_top1, v_top2, v_bot1)
        add_triangle(facets, v_top2, v_bot2, v_bot1)
    # Bottom edge (j = rows - 1)
    j = rows - 1
    for i in range(cols - 1):
        v_top1 = top_vertices[j, i]
        v_top2 = top_vertices[j, i + 1]
        v_bot1 = (v_top1[0], v_top1[1], 0.0)
        v_bot2 = (v_top2[0], v_top2[1], 0.0)
        add_triangle(facets, v_top2, v_top1, v_bot1)
        add_triangle(facets, v_top2, v_bot1, v_bot2)
    # Left edge (i = 0)
    i = 0
    for j in range(rows - 1):
        v_top1 = top_vertices[j, i]
        v_top2 = top_vertices[j + 1, i]
        v_bot1 = (v_top1[0], v_top1[1], 0.0)
        v_bot2 = (v_top2[0], v_top2[1], 0.0)
        add_triangle(facets, v_top2, v_top1, v_bot1)
        add_triangle(facets, v_top2, v_bot1, v_bot2)
    # Right edge (i = cols - 1)
    i = cols - 1
    for j in range(rows - 1):
        v_top1 = top_vertices[j, i]
        v_top2 = top_vertices[j + 1, i]
        v_bot1 = (v_top1[0], v_top1[1], 0.0)
        v_bot2 = (v_top2[0], v_top2[1], 0.0)
        add_triangle(facets, v_top1, v_top2, v_bot1)
        add_triangle(facets, v_top2, v_bot2, v_bot1)

    return facets

def main():
    parser = argparse.ArgumentParser(
        description="Convert a PNG image to a closed STL mesh."
    )
    parser.add_argument("input_image", help="Path to input PNG image")
    parser.add_argument("output_stl", help="Path for output STL file")
    parser.add_argument("--extrude_height", type=float, default=15.0,
                        help="Extrusion height (Z-axis) for solid areas (default: 15.0)")
    parser.add_argument("--x_size", type=float, default=120.0,
                        help="Width (X dimension) of the output STL (default: 120.0)")
    parser.add_argument("--y_size", type=float, default=120.0,
                        help="Depth (Y dimension) of the output STL (default: 120.0)")
    parser.add_argument("--binary", action="store_true",
                        help="Activate binary mode (treat image as black and white)")
    parser.add_argument("--threshold", type=int, default=128,
                        help="Threshold for binary mode (default: 128). Pixels with values below are solid.")
    args = parser.parse_args()

    # Open the image and convert to grayscale.
    img = Image.open(args.input_image).convert("L")
    img_array = np.array(img)

    if args.binary:
        facets = generate_binary_mesh(args, img_array)
    else:
        facets = generate_continuous_mesh(args, img_array)

    # Write the facets to an ASCII STL file.
    with open(args.output_stl, "w") as f:
        f.write("solid model\n")
        for normal, v1, v2, v3 in facets:
            f.write("  facet normal {:.6f} {:.6f} {:.6f}\n".format(*normal))
            f.write("    outer loop\n")
            f.write("      vertex {:.6f} {:.6f} {:.6f}\n".format(*v1))
            f.write("      vertex {:.6f} {:.6f} {:.6f}\n".format(*v2))
            f.write("      vertex {:.6f} {:.6f} {:.6f}\n".format(*v3))
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid model\n")

if __name__ == "__main__":
    main()
