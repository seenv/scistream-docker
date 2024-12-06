# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"

  # Ansible provisioner
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "deploy/playbook.yml"
  end

  # Define the VMs
  config.vm.define :producer do |producer|
    #producer.vm.box = "bento/ubuntu-22.04"

    producer.vm.provider :libvirt do |libvirt|
      libvirt.memory = 2048
      libvirt.cpus = 2
    end

    producer.vm.network :private_network, :ip => '192.168.10.10'
  end

  config.vm.define :producers2 do |producers2|
    #producers2.vm.box = "bento/ubuntu-22.04"

    producers2.vm.provider :libvirt do |libvirt|
      libvirt.memory = 2048
      libvirt.cpus = 2
    end

    producers2.vm.network :private_network, :ip => '192.168.10.11'
    producers2.vm.network :private_network, :ip => '192.168.20.10'
  end

  config.vm.define :consumers2 do |consumers2|
    #consumers2.vm.box = "bento/ubuntu-22.04"

    consumers2.vm.provider :libvirt do |libvirt|
      libvirt.memory = 2048
      libvirt.cpus = 2
    end

    consumers2.vm.network :private_network, :ip => '192.168.20.11'
    consumers2.vm.network :private_network, :ip => '192.168.30.10'
  end

  config.vm.define :consumer do |consumer|
    #consumer.vm.box = "bento/ubuntu-22.04"

    consumer.vm.provider :libvirt do |libvirt|
      libvirt.memory = 2048
      libvirt.cpus = 2
    end

    consumer.vm.network :private_network, :ip => '192.168.30.11'
  end


  # Options for Libvirt Vagrant provider.
  config.vm.provider :libvirt do |libvirt|

    # A hypervisor name to access.
    libvirt.driver = "kvm"

    # The name of the server, where Libvirtd is running.
    # libvirt.host = "localhost"

    # If use ssh tunnel to connect to Libvirt.
    libvirt.connect_via_ssh = false

    # The username and password to access Libvirt. Password is not used when
    # connecting via ssh.
    libvirt.username = "vagrant"
    #libvirt.password = "secret"

    # Libvirt storage pool name, where box image and instance snapshots will
    # be stored.
    libvirt.storage_pool_name = "default"

    # Set a prefix for the machines that's different than the project dir name.
    #libvirt.default_prefix = ''
  end
end


