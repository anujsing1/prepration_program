/**
 * 
 */
package com.calsoft;

import java.util.ArrayList;
import java.util.List;

/**
 * @author govind.gupta
 *
 */
public class TestGenerics {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		Hourse h1 = new Hourse("h1", "Hourse");
		h1.setAge(10);
		Hourse h2 = new Hourse("h2", "Hourse");
		h2.setAge(10);
		Hourse h3 = new Hourse("h3", "Hourse");
		h3.setAge(10);
		
		List list = new ArrayList();
		list.add(h1);
		list.add(h2);
		list.add(h3);
		
		List<Hourse> hourseList = new ArrayList<Hourse>();
		hourseList.add(h1);
		hourseList.add(h2);
		hourseList.add(h3);
		
		Hourse[] hourseArray = new Hourse[3];
		hourseArray[0] = h1;
		hourseArray[1] = h2;
		hourseArray[2] = h3;
		
//		h1.m1(hourses);
		Animal animal = new Animal();
		animal.list(list);
		animal.list(hourseList);
//		animal.list(hourseArray);
		
		animal.listAnimal(list);
//		animal.listAnimal(hourseList);
//		animal.listAnimal(hourseArray);
		
		animal.listExtendsAnimal(list);
		animal.listExtendsAnimal(hourseList);
//		animal.listExtendsAnimal(hourseArray);
		
//		animal.animalArray(list);
//		animal.animalArray(hourseList);
		animal.animalArray(hourseArray);
		
		Hourse h = (Hourse) new Animal();
		h.list(list);
	}

}
