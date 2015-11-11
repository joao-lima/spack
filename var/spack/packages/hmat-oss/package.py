from spack import *
import os

class HmatOss(Package):
    """A H-Matrix C/C++ library"""
    homepage = "https://github.com/jeromerobert/hmat-oss/"

    version('master', git='https://github.com/jeromerobert/hmat-oss.git', branch='master')
    version('hmat-oss-1.1', git='https://github.com/jeromerobert/hmat-oss.git', branch='hmat-oss-1.1')
    version('git-1.1.2', git='https://github.com/jeromerobert/hmat-oss.git', tag='1.1.2')
    version('1.1.2', 'fe52fa22e413be862bec1b44a2b695a566525138', url='https://github.com/jeromerobert/hmat-oss/archive/1.1.2.tar.gz')

    variant('examples', default=True, description='Build examples at installation')

    depends_on("cblas")
    depends_on("lapack")

    def install(self, spec, prefix):
        with working_dir('build', create=True):
            cmake_args = [
                "..",
                "-DCMAKE_INSTALL_PREFIX=../install",
                "-DCMAKE_COLOR_MAKEFILE:BOOL=ON",
                "-DINSTALL_DATA_DIR:PATH=share",
                "-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON"]
            
            if spec.satisfies('+examples'):
                cmake_args.extend(["-DBUILD_EXAMPLES:BOOL=ON"])

            if '^mkl-cblas' in spec or '^mkl-lapack' in spec:
                cmake_args.extend(["-DMKL_DETECT=ON"])
            else:
                cmake_args.extend(["-DMKL_DETECT=OFF"])

                # To force FindCBLAS to find MY cblas
                mf = FileFilter('../CMake/FindCBLAS.cmake')
                mf.filter('\"cblas\"','"%s"' % ";".join(cblaslibname+blaslibname))

                cblas = spec['cblas'].prefix
                cmake_args.extend(["-DCBLAS_INCLUDE_DIRS=" + cblas.include])
                cmake_args.extend(["-DCBLAS_LIBRARY_DIRS=" + cblas.lib])

                blas_libs = ";".join(blaslibname)
                blas = spec['blas'].prefix
                cmake_args.extend(["-DBLAS_LIBRARY_DIRS=" + blas.lib])
                cmake_args.extend(["-DBLAS_LIBRARIES=" + blas_libs])

                lapack_libs = ";".join(lapacklibname)
                lapack = spec['lapack'].prefix
                cmake_args.extend(["-DLAPACK_LIBRARY_DIRS=" + lapack.lib])
                cmake_args.extend(["-DLAPACK_LIBRARIES=" + lapack_libs])

            cmake_args.extend(["-DUSE_DEBIAN_OPENBLAS=OFF"])
            
            cmake_args.extend(std_cmake_args)
            
            cmake(*cmake_args)

            make()
            make("install")
