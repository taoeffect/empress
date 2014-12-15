# -*- mode: ruby -*-

require 'yaml'

Vagrant.configure("2") do |config|
  #
  # Common Settings
  #

  config.vm.hostname = "empress.local"
  config.vm.network "private_network", ip: "172.16.100.2"

  config.vm.provision :ansible do |ansible|
    ansible.playbook = "test.yml"
    ansible.host_key_checking = false
    ansible.extra_vars = { testing: true }

    # ansible.tags = ["blog"]
    # ansible.skip_tags = ["openvpn"]
    ansible.verbose = "vvvv"
  end

  config.vm.provider :virtualbox do |v|
    v.memory = 256
  end

  config.vm.provider :vmware_fusion do |v|
    v.vmx["memsize"] = "256"
  end

  config.vm.provider :digital_ocean do |provider, override|
    override.ssh.private_key_path = "~/.ssh/id_rsa"
    override.vm.box = "digital_ocean"
    override.vm.box_url = "https://github.com/smdahlen/vagrant-digitalocean/raw/master/box/digital_ocean.box"

    provider.ssh_key_name = "TODO"
    provider.token = "TODO"
    provider.image = "debian-7-0-x64"
    provider.region = "nyc3"
    provider.size = "512mb"
  end

  # https://github.com/mitchellh/vagrant-google#quick-start
  config.vm.provider :google do |google, override|
    credentials = YAML.load_file('private/credentials.yml')
    google.google_project_id   = credentials['project_id']
    google.google_client_email = credentials['client_email']
    google.google_key_location = "private/key.p12"

    google.image = "debian-7-wheezy-v20141205"
    google.name = "empress-instance"

    # YOU MUST MANUALLY UPLOAD YOUR SSH PUBLIC KEY VIA GOOGLE'S THINGY:
    #     developers console -> Compute -> Compute Engine -> Metadata -> Tab SSH Keys
    # MAKE SURE THAT THE LAST THING IN YOUR KEY IS THE USERNARM 'deploy' LIKE SO
    # 
    #   ssh-rsa AAL...10M= deploy
    #   
    override.ssh.username = "deploy"
    override.ssh.private_key_path = "~/.ssh/id_rsa"
    override.vm.box = "gce"
    override.vm.box_url = "https://github.com/mitchellh/vagrant-google/raw/master/google.box"
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
