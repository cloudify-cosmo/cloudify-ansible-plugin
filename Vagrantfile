Vagrant.configure("2") do |config|
  config.vm.define "web" do |web|
    web.vm.box = "centos/7"
    web.vm.network "forwarded_port", guest: 8000, host: 8000
    web.vm.network :private_network, ip: "11.0.0.7"
  end
  config.vm.define "db" do |db|
    db.vm.box = "centos/7"
    db.vm.network "forwarded_port", guest: 3306, host: 3306
    db.vm.network :private_network, ip: "11.0.0.8"
  end
  config.vm.define "vpn" do |vpn|
    vpn.vm.box = "ubuntu/trusty64"
    vpn.vm.network :private_network, ip: "11.0.0.9"
  end
  config.vm.define "ellis" do |ellis|
    ellis.vm.box = "ubuntu/trusty64"
    ellis.vm.network :private_network, ip: "11.0.0.10"
  end
  config.vm.define "bono" do |bono|
    bono.vm.box = "ubuntu/trusty64"
    bono.vm.network :private_network, ip: "11.0.0.11"
  end
  config.vm.define "sprout" do |sprout|
    sprout.vm.box = "ubuntu/trusty64"
    sprout.vm.network :private_network, ip: "11.0.0.12"
  end
  config.vm.define "homer" do |homer|
    homer.vm.box = "ubuntu/trusty64"
    homer.vm.network :private_network, ip: "11.0.0.13"
  end
  config.vm.define "homestead" do |homestead|
    homestead.vm.box = "ubuntu/trusty64"
    homestead.vm.network :private_network, ip: "11.0.0.14"
  end
  config.vm.define "ralf" do |ralf|
    ralf.vm.box = "ubuntu/trusty64"
    ralf.vm.network :private_network, ip: "11.0.0.15"
  end
  config.vm.define "bind" do |bind|
    bind.vm.box = "ubuntu/trusty64"
    bind.vm.network :private_network, ip: "11.0.0.16"
  end
end
