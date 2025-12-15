"""
Gait Visualization Utilities - Extracted from Gait base class

Usage:
    from graveyard.utils.gait_plotting import plot_gait

    gait = Trot(...)
    plot_gait(gait)
"""

import matplotlib.pyplot as plt


def plot_gait(gait):
    """
    Plot the step sequences for a gait.

    Args:
        gait: A Gait instance with steps1, steps2 (and optionally steps3, steps4)
    """
    print("leg 1")
    plt.plot(gait.steps1, label=["s1_x", "s1_y", "s1_z"])
    plt.legend()
    plt.show()

    print("leg 2")
    plt.plot(gait.steps2, label=["s2_x", "s2_y", "s2_z"])
    plt.legend()
    plt.show()

    if hasattr(gait, 'steps3') and gait.steps3 is not None:
        print("leg 3")
        plt.plot(gait.steps3, label=["s3_x", "s3_y", "s3_z"])
        plt.legend()
        plt.show()

    if hasattr(gait, 'steps4') and gait.steps4 is not None:
        print("leg 4")
        plt.plot(gait.steps4, label=["s4_x", "s4_y", "s4_z"])
        plt.legend()
        plt.show()


# Alias for backward compatibility
plotit = plot_gait
