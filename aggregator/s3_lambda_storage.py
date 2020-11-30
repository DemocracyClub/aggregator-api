from pipeline.compilers.sass import SASSCompiler

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from pipeline.storage import PipelineMixin
from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticStorage(PipelineMixin, CompressedManifestStaticFilesStorage):
   pass


class LambdaSASSCompiler(SASSCompiler):
    """
    Use libsass's python API for converting scss files to css.

    The normal SASSCompiler opens a subprocess to call scss, but this confuses
    lambda as the script isn't on the PATH.

    """

    def compile_file(self, infile, outfile, outdated=False, force=False):
        for path in settings.STATICFILES_DIRS:
            outfile = outfile.replace(path, "").strip("/")
        import sass

        out_value = sass.compile(
            filename=infile,
            output_style="compressed",
            include_paths=settings.SASS_INCLUDE_PATHS,
        )
        if type(out_value) == bytes:
            out_value = out_value.decode("utf8")

        with staticfiles_storage.open(outfile, "w") as out:
            out.write(out_value)
        return out_value
