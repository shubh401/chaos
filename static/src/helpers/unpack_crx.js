/**
 * Unzips a CRX extension to the target directory.
 *
 * @param {string} extension_path - The path to the CRX extension file.
 * @param {string} target_dir - The directory to extract the CRX extension to.
 * @returns {Promise<void>} A promise that resolves when the extraction is complete.
 */
async function unzip_crx(extension_path, target_dir) {
    const {default: unzip} = await import("unzip-crx-3");
    try {
        unzip(extension_path, target_dir).then(() => {
            console.log("Done!");
        });
    } catch (e) {
        console.error(e);
    } finally {
        return;
    }
}

if (process.argv.length == 4) {
    let extension_path = process.argv[2];
    let target_dir = process.argv[3];
    unzip_crx(extension_path, target_dir);
} else {
    console.log("Invalid arguments! Please provide appropriate arguments.")
}