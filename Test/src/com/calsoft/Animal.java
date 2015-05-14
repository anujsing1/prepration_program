/**
 * 
 */
package com.calsoft;

import java.util.List;

/**
 * @author govind.gupta
 *
 */
public class Animal {
	private String name;
	private String type;
	
	public Animal() {
		// TODO Auto-generated constructor stub
	}
	
	public Animal(String name, String type){
		this.name=name;
		this.type=type;
	}
	
	public Animal display()
	{
		return null;
	}
	
	public void list(List animal){
		System.out.println("List is called");
	}
	
	public void listAnimal(List<Animal> animal){
		System.out.println("Animal List is called");
	}
	
	public void listExtendsAnimal(List<? extends Animal> animal){
		System.out.println("Extended Animal List is called");
	}
	
	public void animalArray(Animal[] animal){
		System.out.println("Animal Array is called");
	}
	
	/**
	 * @return the name
	 */
	public String getName() {
		return name;
	}
	/**
	 * @param name the name to set
	 */
	public void setName(String name) {
		this.name = name;
	}
	/**
	 * @return the type
	 */
	public String getType() {
		return type;
	}
	/**
	 * @param type the type to set
	 */
	public void setType(String type) {
		this.type = type;
	}
}
