from spack import *
import os
from subprocess import call

class Mpf(Package):
    """
    A Parallel Linear Algebra Library.
    Set the environment variable SOFTWARREEPO1 to get the versions.
    """
    homepage = "http://www.google.com"

    try:
        version('nd',     git='hades:/home/falco/Airbus/mpf.git', branch='master')
        repo=os.environ['SOFTWAREREPO1']
        version('master', git=repo+'mpf.git', branch='master')
        version('1.22',   git=repo+'mpf.git', branch='v1.22')
        version('1.22.0', git=repo+'mpf.git', tag='v1.22.0')
    except KeyError:
        pass

    variant('shared', default=True , description='Build MPF as a shared library')
    variant('metis' , default=False, description='Use Metis')
    variant('python', default=False, description='Build MPF python interface')

    depends_on("py-mpi4py", when='+python')
    depends_on("blacs")
    depends_on("blas")
    depends_on("lapack")
    depends_on("scalapack")
    depends_on("metis", when="+metis")
    depends_on("mpi")
    depends_on("mumps +scotch")
    depends_on("pastix")
    depends_on("hmat")

    def install(self, spec, prefix):
        project_dir = os.getcwd()
        DefaultCache = project_dir + '/as-make/CMake/InitialCacheDefault.cmake'

        with working_dir('build', create=True):
            scotch = spec['scotch'].prefix
            mumps = spec['mumps'].prefix
            mpi = spec['mpi'].prefix

            cmake_args = [
                project_dir,
                "-C" + DefaultCache,
                "-DMPI_DIR="+ mpi,
                "-DMPI_C_COMPILER="+mpi+"/bin/mpicc",
                "-DMPI_CXX_COMPILER="+mpi+"/bin/mpicxx",
                "-DMPI_Fortran_COMPILER="+mpi+"/bin/mpif77",
                '-DCMAKE_C_FLAGS=-fopenmp -D_GNU_SOURCE -pthread',
                '-DCMAKE_CXX_FLAGS=-fopenmp -D_GNU_SOURCE -pthread',
                '-DCMAKE_Fortran_FLAGS=-fopenmp -pthread',
                "-DCMAKE_COLOR_MAKEFILE:BOOL=ON",
                "-DINSTALL_DATA_DIR:PATH=share",
                "-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON",
                "-DSCOTCH_INCLUDE_DIRS="+ scotch.include,
                "-DSCOTCH_LIBRARY_DIRS="+ scotch.lib,
                ]

            # to activate the test building
            # cmake_args.extend(["-DMPF_TEST:BOOL=ON"])
            
            if spec.satisfies('+shared'):
                cmake_args.extend(['-DBUILD_SHARED_LIBS=ON'])
            else:
                cmake_args.extend(['-DBUILD_SHARED_LIBS=OFF'])

            if spec.satisfies('+python'):
                cmake_args.extend(['-DMPF_BUILD_PYTHON=ON'])
            else:
                cmake_args.extend(['-DMPF_BUILD_PYTHON=OFF'])

            hmat = spec['hmat'].prefix
            cmake_args.extend(["-DHMAT_DIR=%s/CMake" % hmat.share])
            cmake_args.extend(["-DENABLE_HMAT=ON"])

            try:
                blacs = spec['blacs'].prefix
                cmake_args.extend(["-DBLACS_LIBRARY_DIRS=%s/" % blacs.lib])
            except KeyError:
                filter_file('BLACS REQUIRED', 'BLACS', '../CMakeLists.txt')
            
            pastix = spec['pastix'].prefix
            cmake_args.extend(["-DPASTIX_LIBRARY_DIRS=%s" % pastix.lib])
            cmake_args.extend(["-DPASTIX_INCLUDE_DIRS=%s" % pastix.include])
            cmake_args.extend(["-DENABLE_PASTIX=ON"])

            mumps = spec['mumps'].prefix
            cmake_args.extend(["-DMUMPS_LIBRARY_DIRS=%s" % mumps.lib])
            cmake_args.extend(["-DMUMPS_INCLUDE_DIRS=%s" % mumps.include])
            cmake_args.extend(["-DENABLE_MUMPS=ON"])

            if '^mkl-blas' in spec:
                # cree les variables utilisees par as-make/CMake/FindMKL()
                cmake_args.extend(["-DMKL_DETECT=ON"])
                mklblas = spec['mkl-blas'].prefix
                cmake_args.extend(["-DMKL_LIBRARY_DIRS=%s" % mklblas.lib])
                cmake_args.extend(["-DMKL_INCLUDE_DIRS=%s" % mklblas.include])
                mkl_libs=[]
                for l1 in blaslibname:
                    for l2 in l1.split(' '):
                        if l2.startswith('-l'):
                           mkl_libs.extend([l2[2:]])
                cmake_args.extend(["-DMKL_LIBRARIES=%s" % ";".join(mkl_libs)])
            else:
                cmake_args.extend(["-DMKL_DETECT=OFF"])
                blas_libs = ";".join(blaslibname)
                blas = spec['blas'].prefix
                cmake_args.extend(["-DBLAS_LIBRARY_DIRS=%s/" % blas.lib])
                cmake_args.extend(["-DBLAS_LIBRARIES=%s" % blas_libs])

                lapack_libs = ";".join(lapacklibname)
                lapack = spec['lapack'].prefix
                cmake_args.extend(["-DLAPACK_LIBRARY_DIRS=%s/" % lapack.lib])
                cmake_args.extend(["-DLAPACK_LIBRARIES=%s" % lapack_libs])

            cmake_args.extend(["-DUSE_DEBIAN_OPENBLAS=OFF"])
            
            # if spec.satisfies('+metis'):
                # cmake_args.extend(["-DMETIS_LIBRARY_DIRS="+ spec['metis'].prefix.lib])

            mklroot = os.environ['MKLROOT']
            if mklroot:
                cmake_args.extend(["-DMKL_LIBRARIES=mkl_blacs_lp64;mkl_scalapack_lp64;mkl_intel_lp64;mkl_core;mkl_gnu_thread;"])
                cmake_args.extend(["-DMKL_DETECT=ON;"])
                cmake_args.extend(["-DMKL_INCLUDE_DIRS="+mklroot+"/include"])
                cmake_args.extend(["-DMKL_LIBRARY_DIRS="+mklroot+"/lib/intel64"])
                
                # problem with static library blacs... 
                mf = FileFilter(project_dir + '/as-make/CMake/FindMKL.cmake')
                mf.filter('set\(MKL_LIBRARIES -Wl,--start-group;\$\{MKL_LIBRARIES\};-Wl,--end-group\)','set(MKL_LIBRARIES -Wl,--start-group,--whole-archive;${MKL_LIBRARIES};-Wl,--end-group,--no-whole-archive )')  
           # mklroot=os.environ['MKLROOT']
           #     cmake_args.extend(["-DMKL_DETECT=ON"])
           #     cmake_args.extend(["-DMKL_INCLUDE_DIRS=%s" % os.path.join(mklroot, "include") ])
           #     cmake_args.extend(["-DMKL_LIBRARY_DIRS=%s" % os.path.join(mklroot, "lib/intel64") ] )
           #     if spec.satisfies('%intel'):
           #         cmake_args.extend(["-DMKL_LIBRARIES=mkl_intel_lp64;mkl_intel_thread;mkl_core " ] )
           #     else:
           #         cmake_args.extend(["-DMKL_LIBRARIES=mkl_intel_lp64;mkl_gnu_thread;mkl_core " ] )
           #     cmake_args.extend(["-DBLAS_LIBRARIES=\"\" " ] )


            cmake_args.extend(std_cmake_args)
            cmake(*cmake_args)

            make()
            make("install")
