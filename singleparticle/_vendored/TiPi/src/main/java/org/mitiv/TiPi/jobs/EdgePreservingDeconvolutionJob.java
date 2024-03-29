/**
 *
 */
package org.mitiv.TiPi.jobs;

import org.mitiv.TiPi.array.ShapedArray;
import org.mitiv.TiPi.base.Shape;
import org.mitiv.TiPi.invpb.EdgePreservingDeconvolution;
import org.mitiv.TiPi.optim.OptimTask;
import org.mitiv.TiPi.utils.TiPiHook;

/**
 * @author ferreol
 *
 */
public class EdgePreservingDeconvolutionJob {
    public EdgePreservingDeconvolution solver;//FIXME set protected
    protected TiPiHook iterHook,finalHook;
    protected boolean run=true;

    /**
     * @param dataArray
     * @param psfArray
     * @param wgtArray
     * @param outputShape
     * @param mu
     * @param epsilon
     * @param scale
     * @param positivity
     * @param single
     * @param nbIterDeconv
     * @param iterHook
     * @param finalHook
     */
    public EdgePreservingDeconvolutionJob(ShapedArray dataArray, ShapedArray psfArray, ShapedArray wgtArray,
            Shape outputShape, double mu, double epsilon, double[] scale, boolean positivity,
            boolean single, int nbIterDeconv, TiPiHook iterHook, TiPiHook finalHook){

        solver = new EdgePreservingDeconvolution();

        solver.setForceSinglePrecision(single);

        solver.setRelativeTolerance(0.0);
        solver.setUseNewCode(false);
        solver.setObjectShape(outputShape);
        solver.setPSF(psfArray);
        solver.setData(dataArray);
        solver.setWeights(wgtArray);
        solver.setEdgeThreshold(epsilon);
        solver.setRegularizationLevel(mu);

        solver.setScale(scale);
        solver.setSaveBest(true);
        solver.setLowerBound(positivity ? 0.0 : Double.NEGATIVE_INFINITY);
        solver.setUpperBound(Double.POSITIVE_INFINITY);
        solver.setMaximumIterations(nbIterDeconv);
        solver.setMaximumEvaluations(2*nbIterDeconv);

        this.iterHook = iterHook;
        this.finalHook = finalHook;

    }
    /**
     * Perform deconvolution using objArray as initial guess
     * @param objArray
     * @return deconvolved array
     */
    public ShapedArray deconv(ShapedArray objArray){
        int iter=0;
        run = true;
        solver.setInitialSolution(objArray);

        OptimTask task = solver.start();

        while (run) {
            task = solver.getTask();
            if (task == OptimTask.ERROR) {
                System.err.format("Error: %s\n", solver.getReason());
                break;
            }
            if (task == OptimTask.NEW_X || task == OptimTask.FINAL_X) {
                if(iterHook!=null){
                    iterHook.run(solver,iter++);
                }
                if (task == OptimTask.FINAL_X) {
                    break;
                }
            }
            if (task == OptimTask.WARNING) {
                break;
            }
            solver.iterate();
        }
        objArray = solver.getBestSolution().asShapedArray();
        finalHook.run(solver,iter);
        return objArray;

    }
    /**
     * Emergency stop
     */
    public void abort(){
        run = false;
    }
    /**
     * @param psfArray
     */
    public void updatePsf(ShapedArray psfArray) {
        solver.setPSF(psfArray);
    }
    /**
     * @return running state
     */
    public boolean isRunning() {
        return run;
    }
}
