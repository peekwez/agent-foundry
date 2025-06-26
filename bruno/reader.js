/**
 * Reads a file from the artifacts directory and sets its contents to a variable in the bru object
 * @param {string} fileName - The name of the file to read (without extension)
 * @param {string} varName - The name of the variable to set in the bru object
 * @returns {Promise<void>} - A promise that resolves when the file is read and the variable is set
 * @throws {Error} - If there is an error reading the file
 */
const readFile = async (fileName, varName) => {
    try {
        const fs = require("fs");
        const path = require("path");
        const filePath = path.join(__dirname, `artifacts/${fileName}.txt`);
        const fileBuffer = fs.readFileSync(filePath);
        const fileContents = fileBuffer.toString();
        bru.setVar(varName, fileContents);
        console.log(fileContents.slice(0, 64));
    } catch (error) {
        console.error("An error occurred", error);
        throw error;
    }
};
module.exports = { readFile };
