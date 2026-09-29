const Event = artifacts.require("Event");

module.exports = function(deployer) {
  deployer.deploy(Event);
};
