.. automodule:: Pyjo.Util
    :members:

    .. function:: steady_time()

      ::

          ts = steady_time()

      High resolution time elapsed from an arbitrary fixed point in the past,
      resilient to time jumps if a monotonic clock is available.
