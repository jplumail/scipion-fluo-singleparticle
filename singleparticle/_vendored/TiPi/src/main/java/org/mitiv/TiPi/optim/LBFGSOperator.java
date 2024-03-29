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

import org.mitiv.TiPi.exception.IllegalLinearOperationException;
import org.mitiv.TiPi.exception.IncorrectSpaceException;
import org.mitiv.TiPi.linalg.LinearEndomorphism;
import org.mitiv.TiPi.linalg.LinearOperator;
import org.mitiv.TiPi.linalg.Vector;
import org.mitiv.TiPi.linalg.VectorSpace;

/**
 * Implement limited memory quasi-Newton approximation of the inverse Hessian.
 *
 * The approximation of the inverse of Hessian is based on BFGS (Broyden,
 * Fletcher, Goldfarb & Shanno) updates using the 2-loop recursive algorithm of
 * Strang (described by Nocedal, 1980) combined with a preconditioner (initial
 * approximation of the inverse Hessian) or automatic scalings (along the ideas
 * of Gilbert & Lemaréchal (1989); and Shanno).
 *
 * @author Éric Thiébaut.
 */
public class LBFGSOperator extends LinearEndomorphism {

    /** Do not scale the computed direction. */
    static final int NO_SCALING = 0;

    /**
     * Use Oren-Spedicato approximation of the inverse Hessian.
     *
     * <p> This approximation is a simple scaling by: </p>
     *
     * <pre>
     * gamma = (s'.y)/(y'.y)
     * </pre>
     */
    static final int OREN_SPEDICATO_SCALING = 1;

    /**
     * Use Barzilai-Borwein approximation of the inverse Hessian.
     *
     * <p> This approximation is a simple scaling by: </p>
     *
     * <pre>
     * gamma = (s'.s)/(s'.y)
     * </pre>
     */
    static final int BARZILAI_BORWEIN_SCALING = 2;

    /**
     * Do not update the scaling.
     *
     * <p> TThe scaling is only computed at the first update. </p>
     */
    static final int CONSTANT_SCALING = 4;


    /* There are at most M saved pairs, MP is the actual number of saved pairs
     * and UPDATES is the number of effective updates.  Therefore
     * 0 ≤ MP ≤ min(M, UPDATES).
     */
    protected Vector[] s;   // to store variable changes (steps)
    protected Vector[] y;   // to store gradient changes
    protected final int m;  // maximum number of saved pairs
    protected int mp;       // actual number of saved pairs
    protected int updates;  // number of successful updates
    protected double rho[];
    protected double gamma; // scaling parameter for H0
    protected double alpha[];
    protected LinearOperator H0; /* preconditioner (crude approximation
                                    of the inverse Hessian) */
    protected int rule = OREN_SPEDICATO_SCALING;

    /**
     * Create a limited memory BFGS operator without preconditioner.
     *
     * @param space
     *        The vector space to operate on.
     *
     * @param m
     *        The number of previous updates to memorize.
     */
    public LBFGSOperator(VectorSpace space, int m) {
        super(space);
        this.m = m;
        this.H0 = null;
        allocateWorkspace();
    }

    /**
     * Create a limited memory BFGS operator with a preconditioner.
     *
     * <p> The LBFGS operator just stores a reference to the preconditioner
     * {@code H0} and does not assume that the preconditioner is a constant
     * operator.  It is therefore possible for the caller to adjust the
     * preconditioner at every iteration.  The LBFGS operator will have the
     * same input and output spaces as the preconditioner and can be thought as
     * a refined version of {@code H0}.  The preconditioner {@code H0} will be
     * used <i>in-place</i>, that is with the same source and destination
     * vector, it is the user responsibility to make sure that this is
     * possible.  In addition, if bound constraints are applied to the
     * variables, the preconditioner {@code H0} must be a diagonal operator
     * (this is not checked). </p>
     *
     * @param H0
     *        The preconditioner.
     *
     * @param m
     *        The number of previous updates to memorize.
     */
    public LBFGSOperator(LinearEndomorphism H0, int m) {
        super(H0.getSpace());
        this.m = m;
        this.H0 = H0;
        allocateWorkspace();
    }

    private void allocateWorkspace() {
        s = new Vector[m];
        y = new Vector[m];
        for (int i = 0; i < m; ++i) {
            s[i] = space.create();
            y[i] = space.create();
        }
        alpha = new double[m];
        rho = new double[m];
        mp = 0;
        updates = 0;
        gamma = 1.0;
    }

    /**
     * Reset the operator.
     *
     * <p> Forget all memorized pairs. </p>
     */
    public void reset() {
        mp = 0;
    }

    /**
     * Set the scaling of the initial approximation of the inverse Hessian.
     *
     * <p> The best scaling strategy is probably
     * {@link #OREN_SPEDICATO_SCALING} when no preconditioner {@code H0}
     * is provided. </p>
     *
     * @param value
     *        The strategy to use.
     */
    public void setScaling(int value) {
        rule = value;
    }

    /**
     * Get the current scaling strategy.
     *
     * @return The identifier of the current strategy.
     */
    public int getScaling() {
        return rule;
    }

    /**
     * Set the scaling parameter.
     *
     * <p> This automatically set the scaling strategy to
     * {@link #CONSTANT_SCALING}. </p>
     *
     * @param value
     *        The value of gamma. Must be strictly positive.
     */
    public void setScale(double value) {
        if (value <= 0.0) {
            throw new IllegalArgumentException(
                    "scale factor must be strictly positive");
        }
        gamma = value;
        rule = CONSTANT_SCALING;
    }

    /**
     * Get the scaling parameter.
     *
     * @return The current value of {@code gamma}, the scaling parameter of the
     *         initial approximation of the inverse Hessian (that is the
     *         preconditioner {@code H0}, or the identity if no preconditioner
     *         is given).
     */
    public double getScale() {
        return gamma;
    }

    /**
     * Get slot index of a saved pair of variables and gradient differences.
     *
     * <p> The offset {@code j} must be between {@code 0} and {@code mp}
     * (inclusive); {@code slot(0)} is the index of the slot just after the
     * last saved one, that is the one which will be used for the next update;
     * {@code slot(1)} is the last saved pair (newest one), {@code slot(2)} is
     * the previous pair, ..., {@code slot(mp)} is the oldest saved pair. </p>
     *
     * <p> In principle, {@code j} in the range {@code 1} to {@code mp}
     * (inclusive) is used to apply the operator; while {@code j = 0} is only
     * used to update the operator. </p>
     *
     * @param j
     *        The offset.
     *
     * @return The index of {@code j}-th slot relative to the current
     * iteration.
     *
     */
    protected int slot(int j) {
        if (j < 0 || j > mp) {
            throw new IndexOutOfBoundsException(
                    "BFGS slot index is out of bounds");
        }
        return (updates - j) % m;
    }

    protected Vector s(int j) {
        return s[slot(j)];
    }

    protected Vector y(int j) {
        return y[slot(j)];
    }

    /**
     * Apply L-BFGS operator in-place.
     *
     * <p> Apply the original L-BFGS Strang's two-loop recursion.  This private
     * method assumes that the arguments are correct. </p>
     *
     * @param vec
     *        The vector to which apply the operator (operation is done
     *        in-place).
     *
     * @return The result indicates whether the operation was a success.
     */
    private boolean applyInPlace(Vector vec)
    {
        /* First loop of the recursion. */
        for (int j = 1; j <= mp; ++j) {
            final int k = slot(j);
            if (rho[k] > 0.0) {
                alpha[k] = rho[k]*vec.dot(s[k]);
                vec.add(-alpha[k], y[k]);
            }
        }

        /* Apply initial inverse Hessian approximation. */
        if (H0 != null) {
            H0.apply(vec, vec);
        } else if (gamma != 1.0) {
            vec.scale(gamma);
        }

        /* Second loop of the recursion. */
        for (int j = mp; j >= 1; --j) {
            final int k = slot(j);
            if (rho[k] > 0.0) {
                final double beta = rho[k]*vec.dot(y[k]);
                vec.add(alpha[k] - beta, s[k]);
            }
        }
        return true;
    }

    /**
     * Apply L-BFGS operator in-place.
     *
     * <p> Apply the L-BFGS Strang's two-loop recursion modified to account for
     * free variables.  This private method assumes that the arguments are
     * correct. </p>
     *
     * @param wgt
     *        The weight to use for all inner products.
     *
     * @param vec
     *        The vector to which apply the operator (operation is done
     *        in-place).
     *
     * @return The result indicates whether the operation was a success.
     */
    private boolean applyInPlace(Vector wgt, Vector vec)
    {
        /* First loop of the recursion. */
        boolean flag = (H0 == null);
        gamma = 0.0;
        for (int j = 1; j <= mp; ++j) {
            final int k = slot(j);
            final double sty = wgt.dot(y[k], s[k]);
            if (sty <= 0.0) {
                rho[k] = 0.0;
            } else {
                rho[k] = 1.0/sty;
                alpha[k] = rho[k]*wgt.dot(vec, s[k]);
                vec.add(-alpha[k], y[k]);
                if (flag) {
                    /* No initial inverse Hessian approximation has been
                     * provided, we compute a simple scaling GAMMA. */
                    final double yty = wgt.dot(y[k], y[k]);
                    if (yty > 0.0) {
                        gamma = sty/yty;
                        flag = false;
                    }
                }
            }
        }
        if (flag) {
            /* No valid (s,y) pair found. */
            return false;
        }

        /* Apply initial inverse Hessian approximation. */
        if (H0 != null) {
            H0.apply(vec, vec);
        } else if (gamma != 1) {
            vec.scale(gamma);
        }

        /* Second loop of the recursion. */
        for (int j = mp; j >= 1; --j) {
            final int k = slot(j);
            if (rho[k] > 0) {
                final double beta = rho[k]*wgt.dot(vec, y[k]);
                vec.add(alpha[k] - beta, s[k]);
            }
        }
        return true;
    }

    public boolean apply(Vector wgt, Vector vec, Vector dst)
    {
        if ((wgt != null && ! wgt.belongsTo(space)) ||
                ! vec.belongsTo(space) ||
                ! dst.belongsTo(space)) {
            throw new IncorrectSpaceException();
        }
        if (mp < 1) {
            /* Will use the steepest descent direction. */
            return false;
        }
        if (vec != dst) {
            dst.copy(vec);
        }
        if (wgt == null) {
            return applyInPlace(vec);
        } else {
            return applyInPlace(wgt, vec);
        }

    }

    /* Apply inverse Hessian approximation (out-of-place operation). */
    @Override
    protected void _apply(Vector dst, Vector src, int job) {
        if (job != DIRECT && job != ADJOINT) {
            throw new IllegalLinearOperationException();
        }
        if (dst != src) {
            dst.copy(src);
        }
        applyInPlace(dst);
    }

    /**
     * Update LBFGS operator with a new pair of variables and gradient
     * differences.
     *
     * @param x1
     *        The new variables.
     *
     * @param x0
     *        The previous variables.
     *
     * @param g1
     *        The gradient at {@code x1}.
     *
     * @param g0
     *        The gradient at {@code x0}.
     *
     * @throws IncorrectSpaceException
     */
    public void update(Vector x1, Vector x0, Vector g1, Vector g0)
            throws IncorrectSpaceException {
        update(x1, x0, g1, g0, false);
    }

    /**
     * Update LBFGS operator with a new pair of variables and gradient
     * differences.
     *
     * @param x1
     *        The new variables.
     *
     * @param x0
     *        The previous variables.
     *
     * @param g1
     *        The gradient at {@code x1}.
     *
     * @param g0
     *        The gradient at {@code x0}.
     *
     * @param partial
     *        Perform only partial update?
     *
     * @throws IncorrectSpaceException
     */
    public void update(Vector x1, Vector x0, Vector g1, Vector g0,
            boolean partial) throws IncorrectSpaceException {
        /* Store the variables and gradient differences in the slot
         * just after the mark (which is the index of the last saved
         * pair or -1 if none).
         */
        final int k = slot(0);
        s[k].combine(1.0, x1, -1.0, x0);
        y[k].combine(1.0, g1, -1.0, g0);

        if (partial) {
            /* Do not compute RHO[k] and GAMMA for VMLMB. */
            rho[k] = 0.0;
            gamma = 0.0;
        } else {
            /* Compute RHO[k] and GAMMA.  If the update formula for GAMMA does
             * not yield a strictly positive value, the strategy is to keep the
             * previous value.  FIXME: should we restart? */
            final double sty = s[k].dot(y[k]);
            if (sty <= 0.0) {
                /* This pair will be skipped.  This may however indicate a
                 * problem, see Nocedal & Wright "Numerical Optimization",
                 * section 8.1, p. 201 (1999). */
                rho[k] = 0.0;
                return;
            } else {
                /* Compute RHO[k] and GAMMA. */
                rho[k] = 1.0/sty;
                if (rule == OREN_SPEDICATO_SCALING
                        || (rule == (OREN_SPEDICATO_SCALING|CONSTANT_SCALING) &&
                        updates == 0)) {
                    final double ynorm = y[k].norm2();
                    gamma = (sty/ynorm)/ynorm;
                } else if (rule == BARZILAI_BORWEIN_SCALING
                        || (rule == (BARZILAI_BORWEIN_SCALING|CONSTANT_SCALING) &&
                        updates == 0)) {
                    final double snorm = s[k].norm2();
                    gamma = (snorm/sty)*snorm;
                }
            }
        }

        /* Update the number of updates and of saved pairs. */
        ++updates;
        if (mp < m) {
            ++mp;
        }
    }

}
