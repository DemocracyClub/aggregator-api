from django.conf import settings
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage,
    staticfiles_storage,
)
from pipeline.compilers.sass import SASSCompiler
from pipeline.storage import PipelineMixin


class StaticStorage(PipelineMixin, ManifestStaticFilesStorage):
    pass


class LambdaSASSCompiler(SASSCompiler):
    """
    Use libsass's python API for converting scss files to css.

    The normal SASSCompiler opens a subprocess to call scss, but this confuses
    lambda as the script isn't on the PATH.

    """

    def compile_file(self, infile, outfile, outdated=False, force=False):
        if not outdated:
            with open(outfile) as f:
                return f.read()
        import sass

        out_value = sass.compile(
            filename=infile,
            output_style="compressed",
            include_paths=settings.SASS_INCLUDE_PATHS,
        )
        if isinstance(out_value, bytes):
            out_value = out_value.decode("utf8")

        with staticfiles_storage.open(outfile, "w") as out:
            out.write(out_value)
        return out_value
