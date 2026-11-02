import os


def _required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' is not set. See project.env.example.")
    return value


# -------------------------------------------------------------------------------------------
s3_bucket       = _required_env('MATILLION_S3_BUCKET')
admin_email     = _required_env('MATILLION_ADMIN_EMAIL')
s3_flag_dry_run = 'Dry-Run.txt'
s3_flag_shutdown_allowed_for_ecops_bez_path = 'Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt'
s3_flag_shutdown_allowed_for_ecops_s_path   = '/tmp/' + s3_flag_shutdown_allowed_for_ecops_bez_path
s3_prefix_beginning = 'Matillion-'
# -------------------------------------------------------------------------------------------
