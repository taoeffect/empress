# -*- mode: ruby -*-

Vagrant.configure("2") do |config|
  #
  # Common Settings
  #

  config.vm.hostname = "empress.local"
  config.vm.network "private_network", ip: "172.16.100.2"

  config.vm.provision :ansible do |ansible|
    ansible.playbook = "site.yml"
    ansible.host_key_checking = false
    ansible.extra_vars = { ansible_ssh_user: "vagrant", testing: true }

    # ansible.tags = ["blog"]
    # ansible.skip_tags = ["openvpn"]
    # ansible.verbose = "vvvv"
  end

  config.vm.provider :virtualbox do |v|
    v.memory = 256
  end

  config.vm.provider :vmware_fusion do |v|
    v.vmx["memsize"] = "256"
  end

  #
  # vagrant-cachier
  #
  # Install the plugin by running: vagrant plugin install vagrant-cachier
  # More information: https://github.com/fgrehm/vagrant-cachier
  #

  if Vagrant.has_plugin? "vagrant-cachier"
    config.cache.enable :apt
    config.cache.scope = :box
  end

  #
  # Debian 7 64-bit (officially supported)
  #

  config.vm.define "debian", primary: true do |debian|
    debian.vm.box = "box-cutter/debian76"
  end
end
