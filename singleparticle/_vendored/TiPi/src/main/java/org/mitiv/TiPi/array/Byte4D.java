// *WARNING* This file has been automatically generated by TPP do not edit directly.
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

package org.mitiv.TiPi.array;

import org.mitiv.TiPi.array.impl.FlatByte4D;
import org.mitiv.TiPi.array.impl.StriddenByte4D;
import org.mitiv.TiPi.base.Shape;
import org.mitiv.TiPi.base.Shaped;
import org.mitiv.TiPi.base.Traits;
import org.mitiv.TiPi.base.mapping.ByteFunction;
import org.mitiv.TiPi.base.mapping.ByteScanner;
import org.mitiv.TiPi.exception.IllegalTypeException;
import org.mitiv.TiPi.exception.NonConformableArrayException;
import org.mitiv.TiPi.base.indexing.Range;
import org.mitiv.TiPi.linalg.shaped.DoubleShapedVector;
import org.mitiv.TiPi.linalg.shaped.FloatShapedVector;
import org.mitiv.TiPi.linalg.shaped.ShapedVector;
import org.mitiv.TiPi.random.ByteGenerator;


/**
 * Define class for comprehensive 4-dimensional arrays of byte's.
 *
 * @author Éric Thiébaut.
 */
public abstract class Byte4D extends Array4D implements ByteArray {

    protected Byte4D(int dim1, int dim2, int dim3, int dim4) {
        super(dim1,dim2,dim3,dim4);
    }

    protected Byte4D(int[] dims) {
        super(dims);
    }

    protected Byte4D(Shape shape) {
        super(shape);
    }

    @Override
    public final int getType() {
        return type;
    }

    /**
     * Query the value stored at a given position.
     *
     * @param i1
     *        The index along the 1st dimension.
     *
     * @param i2
     *        The index along the 2nd dimension.
     *
     * @param i3
     *        The index along the 3rd dimension.
     *
     * @param i4
     *        The index along the 4th dimension.
     *
     * @return The value stored at position {@code (i1,i2,i3,i4)}.
     */
    public abstract byte get(int i1, int i2, int i3, int i4);

    /**
     * Set the value at a given position.
     *
     * @param i1
     *        The index along the 1st dimension.
     *
     * @param i2
     *        The index along the 2nd dimension.
     *
     * @param i3
     *        The index along the 3rd dimension.
     *
     * @param i4
     *        The index along the 4th dimension.
     *
     * @param value
     *        The value to store at position {@code (i1,i2,i3,i4)}.
     */
    public abstract void set(int i1, int i2, int i3, int i4, byte value);

    /*=======================================================================*/
    /* Provide default (non-optimized, except for the loop ordering)
     * implementation of methods that can be coded solely with the "set"
     * and "get" methods. */

    @Override
    public void fill(byte value) {
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, value);
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, value);
                        }
                    }
                }
            }
        }
    }

    @Override
    public void increment(byte value) {
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, (byte)(get(i1,i2,i3,i4) + value));
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, (byte)(get(i1,i2,i3,i4) + value));
                        }
                    }
                }
            }
        }
    }

    @Override
    public void decrement(byte value) {
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, (byte)(get(i1,i2,i3,i4) - value));
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, (byte)(get(i1,i2,i3,i4) - value));
                        }
                    }
                }
            }
        }
    }

    @Override
    public void scale(byte value) {
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, (byte)(get(i1,i2,i3,i4) * value));
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, (byte)(get(i1,i2,i3,i4) * value));
                        }
                    }
                }
            }
        }
    }

    @Override
    public void map(ByteFunction function) {
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, function.apply(get(i1,i2,i3,i4)));
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, function.apply(get(i1,i2,i3,i4)));
                        }
                    }
                }
            }
        }
    }

    @Override
    public void fill(ByteGenerator generator) {
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, generator.nextByte());
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, generator.nextByte());
                        }
                    }
                }
            }
        }
    }

    @Override
    public void scan(ByteScanner scanner)  {
        boolean initialized = false;
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            if (initialized) {
                                scanner.update(get(i1,i2,i3,i4));
                            } else {
                                scanner.initialize(get(i1,i2,i3,i4));
                                initialized = true;
                            }
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            if (initialized) {
                                scanner.update(get(i1,i2,i3,i4));
                            } else {
                                scanner.initialize(get(i1,i2,i3,i4));
                                initialized = true;
                            }
                        }
                    }
                }
            }
        }
    }

    @Override
    public final byte[] flatten() {
        return flatten(false);
    }

    @Override
    public int min() {
        int minValue = (int)(get(0,0,0,0) & 0xFF);
        boolean skip = true;
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            if (skip) {
                                skip = false;
                            } else {
                                int value = (int)(get(i1,i2,i3,i4) & 0xFF);
                                if (value < minValue) {
                                    minValue = value;
                                }
                            }
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            if (skip) {
                                skip = false;
                            } else {
                                int value = (int)(get(i1,i2,i3,i4) & 0xFF);
                                if (value < minValue) {
                                    minValue = value;
                                }
                            }
                        }
                    }
                }
            }
        }
        return minValue;
    }

    @Override
    public int max() {
        int maxValue = (int)(get(0,0,0,0) & 0xFF);
        boolean skip = true;
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            if (skip) {
                                skip = false;
                            } else {
                                int value = (int)(get(i1,i2,i3,i4) & 0xFF);
                                if (value > maxValue) {
                                    maxValue = value;
                                }
                            }
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            if (skip) {
                                skip = false;
                            } else {
                                int value = (int)(get(i1,i2,i3,i4) & 0xFF);
                                if (value > maxValue) {
                                    maxValue = value;
                                }
                            }
                        }
                    }
                }
            }
        }
        return maxValue;
    }

    @Override
    public int[] getMinAndMax() {
        int[] result = new int[2];
        getMinAndMax(result);
        return result;
    }

    @Override
    public void getMinAndMax(int[] mm) {
        int minValue = (int)(get(0,0,0,0) & 0xFF);
        int maxValue = minValue;
        boolean skip = true;
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            if (skip) {
                                skip = false;
                            } else {
                                int value = (int)(get(i1,i2,i3,i4) & 0xFF);
                                if (value < minValue) {
                                    minValue = value;
                                }
                                if (value > maxValue) {
                                    maxValue = value;
                                }
                            }
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            if (skip) {
                                skip = false;
                            } else {
                                int value = (int)(get(i1,i2,i3,i4) & 0xFF);
                                if (value < minValue) {
                                    minValue = value;
                                }
                                if (value > maxValue) {
                                    maxValue = value;
                                }
                            }
                        }
                    }
                }
            }
        }
        mm[0] = minValue;
        mm[1] = maxValue;
    }

    @Override
    public int sum() {
        int totalValue = 0;
        if (getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            totalValue += (int)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            totalValue += (int)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        }
        return totalValue;
    }

    @Override
    public double average() {
        return (double)sum()/(double)number;
    }

    /**
     * Convert instance into a Byte4D.
     *
     * <p>The operation is lazy, in the sense that {@code this} is returned if
     * it is already of the requested type.</p>
     *
     * @return A Byte4D whose values has been converted into
     *         byte's from those of {@code this}.
     */
    @Override
    public Byte4D toByte() {
        return this;
    }

    /**
     * Convert instance into a Short4D.
     *
     * <p>The operation is lazy, in the sense that {@code this} is returned if
     * it is already of the requested type.</p>
     *
     * @return A Short4D whose values has been converted into
     *         short's from those of {@code this}.
     */
    @Override
    public Short4D toShort() {
        short[] out = new short[number];
        if (isFlat()) {
            byte[] inp = getData();
            for (int i = 0; i < number; ++i) {
                out[i] = (short)(inp[i] & 0xFF);
            }
        } else {
            int i = -1;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            out[++i] = (short)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        }
        return Short4D.wrap(out, getShape());
    }

    /**
     * Convert instance into an Int4D.
     *
     * <p>The operation is lazy, in the sense that {@code this} is returned if
     * it is already of the requested type.</p>
     *
     * @return An Int4D whose values has been converted into
     *         int's from those of {@code this}.
     */
    @Override
    public Int4D toInt() {
        int[] out = new int[number];
        if (isFlat()) {
            byte[] inp = getData();
            for (int i = 0; i < number; ++i) {
                out[i] = (int)(inp[i] & 0xFF);
            }
        } else {
            int i = -1;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            out[++i] = (int)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        }
        return Int4D.wrap(out, getShape());
    }

    /**
     * Convert instance into a Long4D.
     *
     * <p>The operation is lazy, in the sense that {@code this} is returned if
     * it is already of the requested type.</p>
     *
     * @return A Long4D whose values has been converted into
     *         long's from those of {@code this}.
     */
    @Override
    public Long4D toLong() {
        long[] out = new long[number];
        if (isFlat()) {
            byte[] inp = getData();
            for (int i = 0; i < number; ++i) {
                out[i] = (long)(inp[i] & 0xFF);
            }
        } else {
            int i = -1;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            out[++i] = (long)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        }
        return Long4D.wrap(out, getShape());
    }

    /**
     * Convert instance into a Float4D.
     *
     * <p>The operation is lazy, in the sense that {@code this} is returned if
     * it is already of the requested type.</p>
     *
     * @return A Float4D whose values has been converted into
     *         float's from those of {@code this}.
     */
    @Override
    public Float4D toFloat() {
        float[] out = new float[number];
        if (isFlat()) {
            byte[] inp = getData();
            for (int i = 0; i < number; ++i) {
                out[i] = (float)(inp[i] & 0xFF);
            }
        } else {
            int i = -1;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            out[++i] = (float)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        }
        return Float4D.wrap(out, getShape());
    }

    /**
     * Convert instance into a Double4D.
     *
     * <p>The operation is lazy, in the sense that {@code this} is returned if
     * it is already of the requested type.</p>
     *
     * @return A Double4D whose values has been converted into
     *         double's from those of {@code this}.
     */
    @Override
    public Double4D toDouble() {
        double[] out = new double[number];
        if (isFlat()) {
            byte[] inp = getData();
            for (int i = 0; i < number; ++i) {
                out[i] = (double)(inp[i] & 0xFF);
            }
        } else {
            int i = -1;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            out[++i] = (double)(get(i1,i2,i3,i4) & 0xFF);
                        }
                    }
                }
            }
        }
        return Double4D.wrap(out, getShape());
    }

    @Override
    public Byte4D copy() {
        return new FlatByte4D(flatten(true), shape);
    }

    @Override
    public void assign(ShapedArray arr) {
        if (! getShape().equals(arr.getShape())) {
            throw new NonConformableArrayException("Source and destination must have the same shape");
        }
        Byte4D src;
        if (arr.getType() == Traits.BYTE) {
            src = (Byte4D)arr;
        } else {
            src = (Byte4D)arr.toByte();
        }
        // FIXME: do assignation and conversion at the same time
        if (getOrder() == ROW_MAJOR && src.getOrder() == ROW_MAJOR) {
            for (int i1 = 0; i1 < dim1; ++i1) {
                for (int i2 = 0; i2 < dim2; ++i2) {
                    for (int i3 = 0; i3 < dim3; ++i3) {
                        for (int i4 = 0; i4 < dim4; ++i4) {
                            set(i1,i2,i3,i4, src.get(i1,i2,i3,i4));
                        }
                    }
                }
            }
        } else {
            /* Assume column-major order. */
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, src.get(i1,i2,i3,i4));
                        }
                    }
                }
            }
        }
    }

    @Override
    public void assign(ShapedVector vec) {
        if (! getShape().equals(vec.getShape())) {
            throw new NonConformableArrayException("Source and destination must have the same shape");
        }
        // FIXME: much too slow and may be skipped if data are identical (and array is flat)
        int i = -1;
        if (vec.getType() == Traits.DOUBLE) {
            DoubleShapedVector src = (DoubleShapedVector)vec;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, (byte)src.get(++i));
                        }
                    }
                }
            }
        } else if (vec.getType() == Traits.FLOAT) {
            FloatShapedVector src = (FloatShapedVector)vec;
            for (int i4 = 0; i4 < dim4; ++i4) {
                for (int i3 = 0; i3 < dim3; ++i3) {
                    for (int i2 = 0; i2 < dim2; ++i2) {
                        for (int i1 = 0; i1 < dim1; ++i1) {
                            set(i1,i2,i3,i4, (byte)src.get(++i));
                        }
                    }
                }
            }
        } else {
            throw new IllegalTypeException();
        }
    }


    /*=======================================================================*/
    /* ARRAY FACTORIES */

    @Override
    public Byte4D create() {
        return new FlatByte4D(getShape());
    }

    /**
     * Create a 4D array of byte's with given dimensions.
     *
     * <p> This method creates a 4D array of byte's with zero offset,
     * contiguous elements and column-major order.  All dimensions must at
     * least 1. </p>
     *
     * @param dim1
     *        The 1st dimension of the 4D array.
     *
     * @param dim2
     *        The 2nd dimension of the 4D array.
     *
     * @param dim3
     *        The 3rd dimension of the 4D array.
     *
     * @param dim4
     *        The 4th dimension of the 4D array.
     *
     * @return A new 4D array of byte's.
     *
     * @see Shaped#COLUMN_MAJOR
     */
    public static Byte4D create(int dim1, int dim2, int dim3, int dim4) {
        return new FlatByte4D(dim1,dim2,dim3,dim4);
    }

    /**
     * Create a 4D array of byte's with given shape.
     *
     * <p> This method creates a 4D array of byte's with zero offset,
     * contiguous elements and column-major order. </p>
     *
     * @param dims
     *        The list of dimensions of the 4D array (all dimensions must
     *        at least 1).  This argument is not referenced by the returned
     *        object and its contents can be modified after calling this
     *        method.
     *
     * @return A new 4D array of byte's.
     *
     * @see Shaped#COLUMN_MAJOR
     */
    public static Byte4D create(int[] dims) {
        return new FlatByte4D(dims);
    }

    /**
     * Create a 4D array of byte's with given shape.
     *
     * <p> This method creates a 4D array of byte's with zero offset,
     * contiguous elements and column-major order. </p>
     *
     * @param shape
     *        The shape of the 4D array.
     *
     * @return A new 4D array of byte's.
     *
     * @see Shaped#COLUMN_MAJOR
     */
    public static Byte4D create(Shape shape) {
        return new FlatByte4D(shape);
    }

    /**
     * Wrap an existing array in a 4D array of byte's with given
     * dimensions.
     *
     * <p> The returned 4D array have zero offset, contiguous elements
     * and column-major storage order.  More specifically: </p>
     *
     * <pre>
     * arr.get(i1,i2,i3,i4) = data[i1 + dim1*(i2 + dim2*(i3 + dim3*i4))]
     * </pre>
     *
     * <p> with {@code arr} the returned 4D array. </p>
     *
     * @param data
     *        The data to wrap in the 4D array.
     *
     * @param dim1
     *        The 1st dimension of the 4D array.
     *
     * @param dim2
     *        The 2nd dimension of the 4D array.
     *
     * @param dim3
     *        The 3rd dimension of the 4D array.
     *
     * @param dim4
     *        The 4th dimension of the 4D array.
     *
     * @return A 4D array sharing the elements of <b>data</b>.
     *
     * @see Shaped#COLUMN_MAJOR
     */
    public static Byte4D wrap(byte[] data, int dim1, int dim2, int dim3, int dim4) {
        return new FlatByte4D(data, dim1,dim2,dim3,dim4);
    }

    /**
     * Wrap an existing array in a 4D array of byte's with given
     * shape.
     *
     * <p> The returned 4D array have zero offset, contiguous elements
     * and column-major storage order.  More specifically: </p>
     *
     * <pre>
     * arr.get(i1,i2,i3,i4) = data[i1 + shape[0]*(i2 + shape[1]*(i3 + shape[2]*i4))]
     * </pre>
     *
     * <p> with {@code arr} the returned 4D array. </p>
     *
     * @param data
     *        The data to wrap in the 4D array.
     *
     * @param dims
     *        The list of dimensions of the 4D array.  This argument is
     *        not referenced by the returned object and its contents can be
     *        modified after the call to this method.
     *
     * @return A new 4D array of byte's sharing the elements of
     *         <b>data</b>.
     *
     * @see Shaped#COLUMN_MAJOR
     */
    public static Byte4D wrap(byte[] data, int[] dims) {
        return new FlatByte4D(data, dims);
    }

    /**
     * Wrap an existing array in a 4D array of byte's with given shape.
     *
     * <p> The returned 4D array have zero offset, contiguous elements
     * and column-major storage order.  More specifically: </p>
     *
     * <pre>
     * arr.get(i1,i2,i3,i4) = data[i1 + shape[0]*(i2 + shape[1]*(i3 + shape[2]*i4))]
     * </pre>
     *
     * <p>
     * with {@code arr} the returned 4D array. </p>
     *
     * @param data
     *        The data to wrap in the 4D array.
     *
     * @param shape
     *        The shape of the 4D array.
     *
     * @return A new 4D array of byte's sharing the elements of
     *         <b>data</b>.
     *
     * @see Shaped#COLUMN_MAJOR
     */
    public static Byte4D wrap(byte[] data, Shape shape) {
        return new FlatByte4D(data, shape);
    }

    /**
     * Wrap an existing array in a 4D array of byte's with given
     * dimensions, strides and offset.
     *
     * <p> This creates a 4D array of dimensions {{@code dim1,dim2,dim3,dim4}}
     * sharing (part of) the contents of {@code data} in arbitrary storage
     * order.  More specifically: </p>
     *
     * <pre>
     * arr.get(i1,i2,i3,i4) = data[offset + stride1*i1 + stride2*i2 + stride3*i3 + stride4*i4]
     * </pre>
     *
     * <p> with {@code arr} the returned 4D array. </p>
     *
     * @param data
     *        The array to wrap in the 4D array.
     *
     * @param offset
     *        The offset in {@code data} of element (0,0,0,0) of the
     *        4D array.
     *
     * @param stride1
     *        The stride along the 1st dimension.
     *
     * @param stride2
     *        The stride along the 2nd dimension.
     *
     * @param stride3
     *        The stride along the 3rd dimension.
     *
     * @param stride4
     *        The stride along the 4th dimension.
     *
     * @param dim1
     *        The 1st dimension of the 4D array.
     *
     * @param dim2
     *        The 2nd dimension of the 4D array.
     *
     * @param dim3
     *        The 3rd dimension of the 4D array.
     *
     * @param dim4
     *        The 4th dimension of the 4D array.
     *
     * @return A 4D array sharing the elements of <b>data</b>.
     */
    public static Byte4D wrap(byte[] data,
            int offset, int stride1, int stride2, int stride3, int stride4, int dim1, int dim2, int dim3, int dim4) {
        return new StriddenByte4D(data, offset, stride1,stride2,stride3,stride4, dim1,dim2,dim3,dim4);
    }

    /**
     * Get a slice of the array.
     *
     * @param idx
     *        The index of the slice along the last dimension of the array.
     *        The same indexing rules as for {@link mitiv.base.indexing.Range}
     *        apply for negative index: 0 for the first, 1 for the second, -1
     *        for the last, -2 for penultimate, <i>etc.</i>
     *
     * @return A Byte3D view on the given slice of the array.
     */
    public abstract Byte3D slice(int idx);

    /**
     * Get a slice of the array.
     *
     * @param idx
     *        The index of the slice along the last dimension of the array.
     *
     * @param dim
     *        The dimension to slice.  For these two arguments, the same
     *        indexing rules as for {@link mitiv.base.indexing.Range} apply for
     *        negative index: 0 for the first, 1 for the second, -1 for the
     *        last, -2 for penultimate, <i>etc.</i>
     *
     * @return A Byte3D view on the given slice of the array.
     */
    public abstract Byte3D slice(int idx, int dim);

    /**
     * Get a view of the array for given ranges of indices.
     *
     * @param rng1
     *        The range of indices to select along 1st dimension (or
     *        {@code null} to select all.
     *
     * @param rng2
     *        The range of indices to select along 2nd dimension (or
     *        {@code null} to select all.
     *
     * @param rng3
     *        The range of indices to select along 3rd dimension (or
     *        {@code null} to select all.
     *
     * @param rng4
     *        The range of indices to select along 4th dimension (or
     *        {@code null} to select all.
     *
     * @return A Byte4D view for the given ranges of the array.
     */
    public abstract Byte4D view(Range rng1, Range rng2, Range rng3, Range rng4);

    /**
     * Get a view of the array for given ranges of indices.
     *
     * @param idx1
     *        The list of indices to select along 1st dimension (or
     *        {@code null} to select all.
     *
     * @param idx2
     *        The list of indices to select along 2nd dimension (or
     *        {@code null} to select all.
     *
     * @param idx3
     *        The list of indices to select along 3rd dimension (or
     *        {@code null} to select all.
     *
     * @param idx4
     *        The list of indices to select along 4th dimension (or
     *        {@code null} to select all.
     *
     * @return A Byte4D view for the given index selections of the
     *         array.
     */
    public abstract Byte4D view(int[] idx1, int[] idx2, int[] idx3, int[] idx4);

    /**
     * Get a view of the array as a 1D array.
     *
     * @return A 1D view of the array.
     */
    @Override
    public abstract Byte1D as1D();

}
