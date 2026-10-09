// Signed, overlap-normalized correlation; preserve anti-repeaters.
#include <cmath>
#include <limits>
extern "C" double best_ncc(const double* a, const double* b, int n, int lagmax, int* bestlag) {
    double best=std::numeric_limits<double>::quiet_NaN();
    *bestlag=0;
    for(int lag=-lagmax;lag<=lagmax;lag++) {
        int begin=lag<0?-lag:0, end=lag>0?n-lag:n, m=end-begin;
        if(m<3)continue;
        double sa=0,sb=0;
        for(int i=begin;i<end;i++){sa+=a[i];sb+=b[i+lag];}
        sa/=m;sb/=m;
        double dot=0,aa=0,bb=0;
        for(int i=begin;i<end;i++){
            double x=a[i]-sa,y=b[i+lag]-sb;dot+=x*y;aa+=x*x;bb+=y*y;
        }
        if(aa<=0 || bb<=0)continue;
        double r=dot/std::sqrt(aa*bb);
        if(!std::isfinite(best) || std::abs(r)>std::abs(best)){best=r;*bestlag=lag;}
    }
    return best;
}

// Batch matrix avoids repeated Python/library overhead for real event windows.
extern "C" void pairwise_ncc(const double* windows,int events,int samples,int lagmax,double* out) {
    for(int i=0;i<events;i++) {
        out[i*events+i]=1.;
        for(int j=i+1;j<events;j++) {
            int lag=0;
            double r=best_ncc(windows+i*samples,windows+j*samples,samples,lagmax,&lag);
            out[i*events+j]=out[j*events+i]=r;
        }
    }
}
