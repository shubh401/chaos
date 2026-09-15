from zipfile import ZipFile
from config import *

def extract_crx(source_dir: str, target_dir: str, crx_id: str) -> bool:
    """
    Extracts a CRX package to the target directory.

    Args:
        source_dir (str): The directory containing the CRX package.
        target_dir (str): The directory to extract the CRX package to.
        crx_id (str): The ID of the CRX package to be extracted.

    Returns:
        bool: True if the extraction was successful, False otherwise.
    """
    status = False
    try:
        if ".crx" not in crx_id and ".zip" not in crx_id:
            if not os.path.exists(target_dir + crx_id):
                shutil.copytree(source_dir + crx_id, target_dir + crx_id)
            return True
        if not os.path.exists(source_dir + crx_id):
            logging.warning("Error!: Package not found for extension: " + crx_id)
            return False
        if "_" in crx_id: new_crx_name = crx_id.split("_", 1)[0]
        else: new_crx_name = crx_id[:-4]
        
        if os.path.exists(target_dir + new_crx_name): return True
        unzip_process = subprocess.Popen(["node", CRX_UNPACKER, source_dir + crx_id, target_dir + new_crx_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        unzip_output, unzip_error = unzip_process.stdout.read().decode(), unzip_process.stderr.read().decode()
        if unzip_output == "Error!":
            logging.error("[EXTRACTOR] Error while unzipping crx: " + crx_id)
            status = False
        elif "Does not start with Cr24" in unzip_error:
            status = False
        else: status = True
    except:
        logging.error("[EXTRACTOR] Error while extracting package for extension: " + crx_id + " - " + ", ".join(traceback.format_exc().split("\n")))
        status = False
    return status
        
def extract_xpi(source_dir: str, target_dir: str, xpi_id: str) -> bool:
    """
    Extracts an XPI package to the target directory.

    Args:
        source_dir (str): The directory containing the XPI package.
        target_dir (str): The directory to extract the XPI package to.
        xpi_id (str): The ID of the XPI package to be extracted.

    Returns:
        bool: True if the extraction was successful, False otherwise.
    """
    try:
        if not os.path.exists(source_dir + xpi_id):
            logging.warning("Error: Package not found for extension: " + xpi_id)
            return False

        if os.path.exists(target_dir + xpi_id[:-4]): return True
        with ZipFile(source_dir + xpi_id, 'r') as zip_file:
            os.mkdir(target_dir + xpi_id[:-4])
            zip_file.extractall(target_dir + xpi_id[:-4] + "/")
        return True
    except:
        logging.error("[EXTRACTOR] Error while extracting package for extension: " + xpi_id + " - " + ", ".join(traceback.format_exc().split("\n")))
        return False
   
def extract_package(source_dir: str, target_dir: str, extension_id: str) -> bool:
    """
    Extracts a package (CRX or XPI) to the target directory based on the extension type.

    Args:
        source_dir (str): The directory containing the package.
        target_dir (str): The directory to extract the package to.
        extension_id (str): The ID of the package to be extracted.

    Returns:
        bool: True if the extraction was successful, False otherwise.
    """
    if EXTENSION_TYPE == 'chrome':
        return extract_crx(source_dir, target_dir, extension_id)
    return extract_xpi(source_dir, target_dir, extension_id)
