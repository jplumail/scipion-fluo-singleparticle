/*
 * This file is part of TiPi (a Toolkit for Inverse Problems and Imaging)
 * developed by the MitiV project.
 *
 * Copyright (c) 2014 the MiTiV project, http://mitiv.univ-lyon1.fr/
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

package org.mitiv.TiPi.optim;

import org.mitiv.TiPi.base.Traits;
import org.mitiv.TiPi.linalg.Vector;
import org.mitiv.TiPi.linalg.shaped.DoubleShapedVector;
import org.mitiv.TiPi.linalg.shaped.FloatShapedVector;
import org.mitiv.TiPi.linalg.shaped.ShapedVectorSpace;

/**
 * Implements a simple bounds projector.
 *
 * The bound is a scalar, it has the same value for all the variables.
 *
 * @author Éric Thiébaut.
 */
public class SimpleBounds extends BoundProjector {

    /** The lower bound. */
    private final double lowerBound;

    /** The upper bound. */
    private final double upperBound;

    /** Use single precision? */
    private final boolean single;

    /**
     * Create a projector with scalar upper bound.
     * @param vsp        - The input and output vector space for the variables.
     * @param upperBound - The value of the upper bound.
     * @param lowerBound - The value of the lower bound.
     */
    public SimpleBounds(ShapedVectorSpace vsp, double lowerBound, double upperBound) {
        super(vsp);
        if (vsp.getType() == Traits.DOUBLE) {
            single = false;
        } else if (vsp.getType() == Traits.FLOAT) {
            single = true;
        } else {
            throw new IllegalArgumentException("Only double/double type supported");
        }
        checkBounds(lowerBound, upperBound, single);
        this.lowerBound = lowerBound;
        this.upperBound = upperBound;
    }

    public double getUpperBound() {
        return upperBound;
    }

    public double getLowerBound() {
        return lowerBound;
    }

    @Override
    protected void _projectVariables(Vector dst, Vector src) {
        final int n = src.getNumber();
        if (single) {
            final float xmin = convertToFloat(getLowerBound());
            final float xmax = convertToFloat(getUpperBound());
            float[] x    = ((FloatShapedVector)src).getData();
            float[] xp   = ((FloatShapedVector)dst).getData();
            for (int j = 0; j < n; ++j) {
                xp[j] = clamp(x[j], xmin, xmax);
            }
        } else {
            final double xmin = getLowerBound();
            final double xmax = getUpperBound();
            double[] x    = ((DoubleShapedVector)src).getData();
            double[] xp   = ((DoubleShapedVector)dst).getData();
            for (int j = 0; j < n; ++j) {
                xp[j] = clamp(x[j], xmin, xmax);
            }
        }
    }

    @Override
    protected void _projectDirection(Vector vx, Vector vd, boolean ascent,
            Vector vdp, double[] bnd) {
        final int n = vx.getNumber();
        if (single) {
            final float zero = 0;
            final float xmin = convertToFloat(getLowerBound());
            final float xmax = convertToFloat(getUpperBound());
            float[] x    = ((FloatShapedVector)vx).getData();
            float[] d    = ((FloatShapedVector)vd).getData();
            float[] dp   = ((FloatShapedVector)vdp).getData();
            if (bnd == null) {
                /* Step length bounds not required. */
                if (ascent) {
                    /* Ascent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] < zero) {
                            /* Variable will increase. */
                            dp[j] = (x[j] < xmax ? d[j] : zero);
                        } else if (d[j] > zero) {
                            /* Variable will decrease. */
                            dp[j] = (x[j] > xmin ? d[j] : zero);
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                } else {
                    /* Descent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] > zero) {
                            /* Variable will increase. */
                            dp[j] = (x[j] < xmax ? d[j] : zero);
                        } else if (d[j] < zero) {
                            /* Variable will decrease. */
                            dp[j] = (x[j] > xmin ? d[j] : zero);
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                }
            } else {
                /* Compute step length bounds. */
                float tmp, amin = Float.POSITIVE_INFINITY, amax = zero;
                if (ascent) {
                    /* Ascent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] < zero) {
                            /* Variable will increase. */
                            if (x[j] < xmax) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmax == Float.POSITIVE_INFINITY) {
                                    amax = Float.POSITIVE_INFINITY;
                                } else {
                                    tmp = (x[j] - xmax)/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else if (d[j] > zero) {
                            /* Variable will decrease. */
                            if (x[j] > xmin) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmin == Float.NEGATIVE_INFINITY) {
                                    amax = Float.POSITIVE_INFINITY;
                                } else {
                                    tmp = (x[j] - xmin)/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                } else {
                    /* Descent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] > zero) {
                            /* Variable will increase. */
                            if (x[j] < xmax) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmax == Float.POSITIVE_INFINITY) {
                                    amax = Float.POSITIVE_INFINITY;
                                } else {
                                    tmp = (xmax - x[j])/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else if (d[j] < zero) {
                            /* Variable will decrease. */
                            if (x[j] > xmin) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmin == Float.NEGATIVE_INFINITY) {
                                    amax = Float.POSITIVE_INFINITY;
                                } else {
                                    tmp = (xmin - x[j])/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                }
                bnd[0] = amin;
                bnd[1] = amax;
            }

        } else {
            final double zero = 0;
            final double xmin = getLowerBound();
            final double xmax = getUpperBound();
            double[] x    = ((DoubleShapedVector)vx).getData();
            double[] d    = ((DoubleShapedVector)vd).getData();
            double[] dp   = ((DoubleShapedVector)vdp).getData();
            if (bnd == null) {
                /* Step length bounds not required. */
                if (ascent) {
                    /* Ascent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] < zero) {
                            /* Variable will increase. */
                            dp[j] = (x[j] < xmax ? d[j] : zero);
                        } else if (d[j] > zero) {
                            /* Variable will decrease. */
                            dp[j] = (x[j] > xmin ? d[j] : zero);
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                } else {
                    /* Descent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] > zero) {
                            /* Variable will increase. */
                            dp[j] = (x[j] < xmax ? d[j] : zero);
                        } else if (d[j] < zero) {
                            /* Variable will decrease. */
                            dp[j] = (x[j] > xmin ? d[j] : zero);
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                }
            } else {
                /* Compute step length bounds. */
                double tmp, amin = Double.POSITIVE_INFINITY, amax = zero;
                if (ascent) {
                    /* Ascent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] < zero) {
                            /* Variable will increase. */
                            if (x[j] < xmax) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmax == Double.POSITIVE_INFINITY) {
                                    amax = Double.POSITIVE_INFINITY;
                                } else {
                                    tmp = (x[j] - xmax)/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else if (d[j] > zero) {
                            /* Variable will decrease. */
                            if (x[j] > xmin) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmin == Double.NEGATIVE_INFINITY) {
                                    amax = Double.POSITIVE_INFINITY;
                                } else {
                                    tmp = (x[j] - xmin)/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                } else {
                    /* Descent direction. */
                    for (int j = 0; j < n; ++j) {
                        if (d[j] > zero) {
                            /* Variable will increase. */
                            if (x[j] < xmax) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmax == Double.POSITIVE_INFINITY) {
                                    amax = Double.POSITIVE_INFINITY;
                                } else {
                                    tmp = (xmax - x[j])/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else if (d[j] < zero) {
                            /* Variable will decrease. */
                            if (x[j] > xmin) {
                                /* Variable is unbound. */
                                dp[j] = d[j];
                                if (xmin == Double.NEGATIVE_INFINITY) {
                                    amax = Double.POSITIVE_INFINITY;
                                } else {
                                    tmp = (xmin - x[j])/d[j];
                                    if (tmp < amin) {
                                        amin = tmp;
                                    }
                                    if (tmp > amax) {
                                        amax = tmp;
                                    }
                                }
                            } else {
                                /* Variable is bound. */
                                dp[j] = zero;
                            }
                        } else {
                            /* Variable will not change. */
                            dp[j] = zero;
                        }
                    }
                }
                bnd[0] = amin;
                bnd[1] = amax;
            }
        }
    }

}

/*
 * Local Variables:
 * mode: Java
 * tab-width: 8
 * indent-tabs-mode: nil
 * c-basic-offset: 4
 * fill-column: 78
 * coding: utf-8
 * ispell-local-dictionary: "american"
 * End:
 */
