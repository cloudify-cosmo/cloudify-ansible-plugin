Vagrant.configure("2") do |config|
  config.vm.define "web" do |web|
    web.vm.box = "centos/7"
    web.vm.network "forwarded_port", guest: 8000, host: 8000
    web.vm.network :private_network, ip: "11.0.0.7"
    web.vm.provision "file", source: "~/.ssh/id_rsa.pub", destination: "~/.ssh/me.pub"
  end
  config.vm.define "db" do |db|
    db.vm.box = "centos/7"
    db.vm.network "forwarded_port", guest: 3306, host: 3306
    db.vm.network :private_network, ip: "11.0.0.8"
    db.vm.provision "file", source: "~/.ssh/id_rsa.pub", destination: "~/.ssh/me.pub"
  end
  config.vm.define "vpn" do |vpn|
    vpn.vm.box = "ubuntu/trusty64"
    vpn.vm.network :private_network, ip: "11.0.0.9"
    vpn.vm.provision "file", source: "~/.ssh/id_rsa.pub", destination: "~/.ssh/me.pub"
  end
end
